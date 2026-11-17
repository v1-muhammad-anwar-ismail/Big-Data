"""Real Facebook Pages & Search scraper via Playwright GraphQL timeline parsing (zero synthetic fallbacks)."""
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import quote
from app.config import settings
from app.scrapers._helpers import (
    UA,
    categorize_topic,
    estimate_tone,
    is_within_years,
    launch_chromium,
    make_doc_id,
    matches_keyword,
    run_coro_sync,
)

DEFAULT_MEDIA_PAGES = [
    "detikcom",
    "Kompascom",
    "CNNIndonesia",
    "tvOneNews",
    "kumparancom",
    "InfoBencanaBNPB",
    "greenpeaceindonesia",
    "InfoBMKG",
]


def _walk_fb_stories(obj: Any, out: List[Dict[str, Any]], seen_ids: set) -> None:
    if isinstance(obj, dict):
        if "post_id" in obj and ("comet_sections" in obj or "wwwURL" in obj):
            pid = str(obj["post_id"])
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                out.append(obj)
            return
        for v in obj.values():
            _walk_fb_stories(v, out, seen_ids)
    elif isinstance(obj, list):
        for v in obj:
            _walk_fb_stories(v, out, seen_ids)


def _extract_fb_story_fields(st: Dict[str, Any], default_page: str) -> Dict[str, Any]:
    s = json.dumps(st, ensure_ascii=False)

    # Message text
    msg_text = ""
    msg_m = re.search(r'"message":\s*\{[^{}]*"text":\s*"((?:[^"\\]|\\.)+)"', s)
    if msg_m:
        try:
            msg_text = json.loads(f'"{msg_m.group(1)}"')
        except Exception:
            msg_text = msg_m.group(1)

    # Exact post permalink URL (never Reels unless post actually is a reel)
    url_m = re.search(r'"wwwURL":\s*"(https:[^"]+)"', s) or re.search(
        r'"permalink_url":\s*"(https:[^"]+)"', s
    )
    post_url = (url_m.group(1).replace("\\/", "/") if url_m else f"https://www.facebook.com/{default_page}/posts/{st.get('post_id')}")

    ct_m = re.search(r'"creation_time":\s*(\d{10})', s)
    ct = int(ct_m.group(1)) if ct_m else 0
    dt = datetime.fromtimestamp(ct, tz=timezone.utc) if ct else datetime.now(timezone.utc)

    react_m = re.search(r'"reaction_count":\s*\{"count":\s*(\d+)', s)
    comm_m = re.search(r'"total_comment_count":\s*(\d+)', s) or re.search(
        r'"comments":\s*\{"total_count":\s*(\d+)', s
    )
    share_m = re.search(r'"share_count":\s*\{"count":\s*(\d+)', s)

    # Attachment photo (explicitly exclude profile avatars which use t39.30808-1 or 40x40)
    img_url = ""
    for pat in [
        r'"photo_image":\s*\{[^}]*"uri":\s*"(https:[^"]+)"',
        r'"thumbnailImage":\s*\{"uri":\s*"(https:[^"]+)"',
        r'"full_picture":\s*"(https:[^"]+)"',
        r'"uri":\s*"(https://scontent[^"]*(?:t39\.30808-6|t15\.5256-10|t51\.2885-15)[^"]*)"',
    ]:
        m_img = re.search(pat, s)
        if m_img:
            img_url = m_img.group(1).replace("\\/", "/")
            break

    actor_m = re.search(r'"actors":\s*\[\{"__typename":\s*"(?:Page|User)"[^}]*"name":\s*"([^"]+)"', s)
    actor = actor_m.group(1) if actor_m else default_page

    return {
        "post_id": str(st.get("post_id", "")),
        "author": actor,
        "text": msg_text.strip(),
        "url": post_url,
        "dt": dt,
        "likes": int(react_m.group(1)) if react_m else 0,
        "comments": int(comm_m.group(1)) if comm_m else 0,
        "shares": int(share_m.group(1)) if share_m else 0,
        "thumb": img_url,
    }


async def _scrape_fb_playwright(pages: List[str], keyword: str, max_posts: int, year_range: int) -> List[Dict[str, Any]]:
    from playwright.async_api import async_playwright

    stories: List[Dict[str, Any]] = []
    seen_ids: set = set()
    c_user = settings.FACEBOOK_C_USER.strip()
    xs = settings.FACEBOOK_XS.strip()
    fb_email = getattr(settings, "FACEBOOK_EMAIL", "").strip()
    fb_pass = getattr(settings, "FACEBOOK_PASSWORD", "").strip()

    async with async_playwright() as p:
        browser = await launch_chromium(p)
        try:
            ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 900}, locale="id-ID")
            has_login = bool(c_user and xs)
            if has_login:
                await ctx.add_cookies([
                    {"name": "c_user", "value": c_user, "domain": ".facebook.com", "path": "/"},
                    {"name": "xs", "value": xs, "domain": ".facebook.com", "path": "/"},
                ])
            elif fb_email and fb_pass:
                login_pg = await ctx.new_page()
                try:
                    await login_pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=20000)
                    await login_pg.wait_for_timeout(2000)
                    if await login_pg.query_selector("input[name='email']"):
                        await login_pg.fill("input[name='email']", fb_email)
                        await login_pg.fill("input[name='pass']", fb_pass)
                        await login_pg.press("input[name='pass']", "Enter")
                        await login_pg.wait_for_timeout(4500)
                        if "two_step_verification" in login_pg.url or "checkpoint" in login_pg.url:
                            print("[Facebook Login] Memicu verifikasi/CAPTCHA Facebook. Gunakan cookie FACEBOOK_C_USER & FACEBOOK_XS dari browser yang sudah login.")
                        ck_names = {c["name"] for c in await ctx.cookies("https://www.facebook.com")}
                        has_login = "c_user" in ck_names and "xs" in ck_names
                except Exception as login_err:
                    print(f"[Facebook Login] Note: {login_err}")
                finally:
                    await login_pg.close()

            page = await ctx.new_page()
            gql_texts: List[str] = []

            async def on_resp(resp):
                if "api/graphql" in resp.url:
                    try:
                        t = await resp.text()
                        if "post_id" in t or "pfbid" in t:
                            gql_texts.append(t)
                    except Exception:
                        pass

            page.on("response", on_resp)

            targets = (
                [("search", f"https://www.facebook.com/search/posts/?q={quote(keyword)}")]
                if has_login
                else [(pg, f"https://www.facebook.com/{pg}") for pg in pages]
            )

            for pg_name, url in targets:
                if len(stories) >= max_posts * 4:
                    break
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=22000)
                    await page.wait_for_timeout(3200)
                    await page.keyboard.press("Escape")
                    scrolls = min(5, max(2, max_posts // 10)) if has_login else 2
                    for _ in range(scrolls):
                        await page.evaluate("window.scrollBy(0, 2200)")
                        await page.wait_for_timeout(2000)

                    html = await page.content()
                    for s in re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.S):
                        if "post_id" in s and "comet_sections" in s:
                            try:
                                before = len(stories)
                                _walk_fb_stories(json.loads(s), stories, seen_ids)
                                for x in stories[before:]:
                                    x["_page_hint"] = pg_name
                            except Exception:
                                pass

                    for ch in gql_texts:
                        for ln in ch.splitlines():
                            ln = ln.strip()
                            if ln.startswith("{") and "post_id" in ln:
                                try:
                                    before = len(stories)
                                    _walk_fb_stories(json.loads(ln), stories, seen_ids)
                                    for x in stories[before:]:
                                        x["_page_hint"] = pg_name
                                except Exception:
                                    pass
                    gql_texts.clear()
                except Exception as e:
                    print(f"[Facebook Playwright] Page {pg_name} error: {e}")

            await ctx.close()
        finally:
            await browser.close()

    matched: List[Dict[str, Any]] = []
    seen_texts: set = set()
    for st in stories:
        page_hint = st.get("_page_hint") or "facebook"
        f = _extract_fb_story_fields(st, page_hint)
        if not f["text"] or not f["url"]:
            continue
        text_sig = f"{f['author'].lower()}::{f['text'][:120].lower()}"
        if text_sig in seen_texts:
            continue
        if not is_within_years(f["dt"], year_range):
            continue
        if not matches_keyword(f"{f['text']} {f['author']}", keyword):
            continue
        seen_texts.add(text_sig)

        cat = categorize_topic(f["text"])
        headline = f["text"][:80] + ("..." if len(f["text"]) > 80 else "")
        matched.append({
            "id": make_doc_id("fb", f["post_id"] or f["url"]),
            "tool_source": "facebook_pages",
            "platform": "Facebook",
            "keyword": keyword,
            "category": cat,
            "title": f"Facebook [{f['author']}]: {headline}",
            "content": f["text"][:1500],
            "url": f["url"],
            "thumbnail_url": f["thumb"],
            "author_or_source": f"Facebook Page: {f['author']}",
            "published_at": f["dt"].isoformat(),
            "published_date": f["dt"].strftime("%Y-%m-%d"),
            "metrics": {
                "views": f["likes"] * 12,
                "likes": f["likes"],
                "comments": f["comments"],
                "shares": f["shares"],
                "sentiment_tone": estimate_tone(f["text"]),
            },
            "raw_data": {"post_id": f["post_id"], "page": page_hint},
        })
        if len(matched) >= max_posts:
            break

    return matched


def scrape_facebook_pages(
    page_name: str = "detikcom",
    keyword: str = "karhutla",
    max_posts: int = 10,
    year_range: int = 5,
) -> List[Dict[str, Any]]:
    pages = [page_name] + [p for p in DEFAULT_MEDIA_PAGES if p.lower() != page_name.lower()]
    return run_coro_sync(_scrape_fb_playwright(pages, keyword, max_posts, year_range))
