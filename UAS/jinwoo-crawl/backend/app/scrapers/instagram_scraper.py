"""Real Instagram scraper: Instaloader (with optional sessionid/login) + Playwright public profile/tag extraction."""
import asyncio
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlsplit
from app.config import settings
from app.scrapers._helpers import (
    UA,
    categorize_topic,
    estimate_tone,
    get_browser_ua,
    is_spam_or_judol,
    is_within_years,
    launch_chromium,
    make_doc_id,
    matches_keyword,
    run_coro_sync,
)

DEFAULT_IG_NEWS_ACCOUNTS = [
    "detikcom",
    "kompascom",
    "cnnindonesia",
    "tribunnews",
    "tribun_video",
    "kumparancom",
    "tempodotco",
    "liputan6",
    "matanajwa",
    "narasinewsroom",
    "bnpb_indonesia",
    "infobmkg",
]


def _build_ig_item(
    *,
    code: str,
    owner: str,
    caption: str,
    keyword: str,
    post_url: str,
    thumbnail_url: str,
    dt: datetime,
    likes: int = 0,
    comments: int = 0,
    views: int = 0,
    extra_raw: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    clean_cap = (caption or "").strip()
    clean_owner = (owner or "instagram").lstrip("@") or "instagram"
    headline = clean_cap[:80] + ("..." if len(clean_cap) > 80 else "")
    raw_data: Dict[str, Any] = {"shortcode": code, "owner": clean_owner}
    if extra_raw:
        raw_data.update(extra_raw)
    return {
        "id": make_doc_id("ig", code),
        "tool_source": "instaloader",
        "platform": "Instagram",
        "keyword": keyword,
        "category": categorize_topic(clean_cap or keyword),
        "title": f"Instagram @{clean_owner}: {headline}" if headline else f"Instagram @{clean_owner}",
        "content": clean_cap[:1500] or f"Postingan Instagram @{clean_owner} terkait {keyword}.",
        "url": post_url,
        "thumbnail_url": thumbnail_url or "",
        "author_or_source": f"@{clean_owner}",
        "published_at": dt.isoformat(),
        "published_date": dt.strftime("%Y-%m-%d"),
        "metrics": {
            "views": views if views > 0 else max(0, likes) * 6,
            "likes": max(0, likes),
            "comments": max(0, comments),
            "shares": 0,
            "sentiment_tone": estimate_tone(clean_cap),
        },
        "raw_data": raw_data,
    }


def _extract_xdt_media_dicts(obj: Any, out: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Recursively collect GraphQL XDTMediaDict / post objects from Instagram /api/graphql JSON."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        if obj.get("__typename") == "XDTMediaDict" or (
            isinstance(obj.get("code"), str) and ("caption" in obj or "taken_at" in obj)
        ):
            out.append(obj)
        for v in obj.values():
            _extract_xdt_media_dicts(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _extract_xdt_media_dicts(v, out)
    return out

_ID_MONTHS = {
    "january": 1, "januari": 1, "february": 2, "februari": 2, "march": 3, "maret": 3,
    "april": 4, "may": 5, "mei": 5, "june": 6, "juni": 6, "july": 7, "juli": 7,
    "august": 8, "agustus": 8, "september": 9, "october": 10, "oktober": 10,
    "november": 11, "december": 12, "desember": 12,
}


def _parse_ig_count(token: str) -> int:
    s = (token or "").strip().upper().replace(",", "")
    if s.endswith("K"):
        return int(float(s[:-1] or 0) * 1000)
    if s.endswith("M"):
        return int(float(s[:-1] or 0) * 1_000_000)
    digits = re.sub(r"[^\d]", "", s)
    return int(digits or 0)


def _parse_ig_og_description(og_desc: str) -> Dict[str, Any]:
    # Examples:
    # '278 likes, 53 comments - detikcom pada November 16, 2026: "Kursi Wakil Presiden..."'
    # '11K likes, 1,425 comments - detikcom on November 16, 2026: "Caption..."'
    likes = 0
    comments = 0
    m_lc = re.search(r"([\d.,]+[KMkm]?)\s*likes?,\s*([\d.,]+[KMkm]?)\s*comments?", og_desc or "", re.I)
    if m_lc:
        likes = _parse_ig_count(m_lc.group(1))
        comments = _parse_ig_count(m_lc.group(2))

    dt = datetime.now(timezone.utc)
    m_dt = re.search(r"(?:on|pada)\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})", og_desc or "", re.I)
    if m_dt:
        mon = _ID_MONTHS.get(m_dt.group(1).lower())
        if mon:
            try:
                dt = datetime(int(m_dt.group(3)), mon, int(m_dt.group(2)), tzinfo=timezone.utc)
            except ValueError:
                pass

    caption = (og_desc or "").strip()
    m_cap = re.search(r"\d{4}\s*:\s*[\"“](.+)", caption, re.S)
    if m_cap:
        caption = re.sub(r"[\"”]\.?\s*$", "", m_cap.group(1)).strip()

    m_author = re.search(r"comments?\s*-\s*([A-Za-z0-9_.]+)\s+(?:pada|on)\s+", og_desc or "", re.I)
    author = m_author.group(1) if m_author else ""

    return {"likes": likes, "comments": comments, "dt": dt, "caption": caption, "author": author}


def _try_instaloader_real(keyword: str, max_posts: int, year_range: int) -> List[Dict[str, Any]]:
    """Use Instaloader if sessionid cookie or valid credentials allow real GraphQL access."""
    sessionid = settings.INSTAGRAM_SESSIONID.strip()
    username = settings.INSTAGRAM_USERNAME.strip()
    password = settings.INSTAGRAM_PASSWORD.strip()
    if not sessionid and not (username and password):
        return []

    results: List[Dict[str, Any]] = []
    try:
        import instaloader

        L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_comments=False,
            save_metadata=False,
            quiet=True,
            max_connection_attempts=1,
        )
        if sessionid:
            L.context._session.cookies.set("sessionid", sessionid, domain=".instagram.com")
        elif username and password:
            L.login(username, password)

        clean_tag = re.sub(r"[^a-zA-Z0-9_]", "", keyword)
        if not clean_tag:
            return []

        hashtag = instaloader.Hashtag.from_name(L.context, clean_tag)
        for post in hashtag.get_posts():
            dt = post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc else datetime.now(timezone.utc)
            if not is_within_years(dt, year_range):
                break
            caption = (post.caption or "").strip()
            owner = getattr(post, "owner_username", None) or clean_tag
            post_url = f"https://www.instagram.com/{'reel' if post.is_video else 'p'}/{post.shortcode}/"
            results.append(
                _build_ig_item(
                    code=post.shortcode,
                    owner=owner,
                    caption=caption,
                    keyword=keyword,
                    post_url=post_url,
                    thumbnail_url=getattr(post, "url", "") or "",
                    dt=dt,
                    likes=int(post.likes or 0),
                    comments=int(post.comments or 0),
                    extra_raw={"is_video": post.is_video},
                )
            )
            if len(results) >= max_posts:
                break
    except Exception as e:
        print(f"[Instaloader API] Note: {e}")

    return results


def _is_ig_gate_url(url: str) -> bool:
    low = (url or "").lower()
    if "/accounts/login" in low or "/challenge" in low or "/accounts/suspended" in low:
        return True
    try:
        sp = urlsplit(low)
        return "instagram.com" in sp.netloc and sp.path.strip("/") == ""
    except Exception:
        return False


def _xdt_to_ig_item(m: Dict[str, Any], keyword: str) -> Optional[Dict[str, Any]]:
    code = str(m.get("code") or "").strip()
    if not code:
        return None
    cap_obj = m.get("caption")
    caption = (cap_obj.get("text") if isinstance(cap_obj, dict) else (cap_obj if isinstance(cap_obj, str) else "")) or ""
    if not caption.strip():
        caption = str(m.get("accessibility_caption") or "").strip()

    user_obj = m.get("user")
    owner = (user_obj.get("username") if isinstance(user_obj, dict) else "") or "instagram"

    taken_at = int(m.get("taken_at") or m.get("taken_at_timestamp") or 0)
    dt = datetime.fromtimestamp(taken_at, tz=timezone.utc) if taken_at > 0 else datetime.now(timezone.utc)

    likes = int(m.get("like_count") or 0)
    comments = int(m.get("comment_count") or 0)
    views = int(m.get("view_count") or m.get("play_count") or 0)

    thumb = ""
    img_v2 = m.get("image_versions2")
    if isinstance(img_v2, dict):
        cands = img_v2.get("candidates")
        if isinstance(cands, list) and cands and isinstance(cands[0], dict):
            thumb = str(cands[0].get("url") or "")

    kind = "reel" if (m.get("video_versions") or int(m.get("media_type") or 1) == 2) else "p"
    post_url = f"https://www.instagram.com/{kind}/{code}/"
    return _build_ig_item(
        code=code,
        owner=owner,
        caption=caption,
        keyword=keyword,
        post_url=post_url,
        thumbnail_url=thumb,
        dt=dt,
        likes=likes,
        comments=comments,
        views=views,
        extra_raw={"from_graphql": True},
    )


async def _scrape_instagram_playwright(keyword: str, max_posts: int, year_range: int) -> List[Dict[str, Any]]:
    from playwright.async_api import async_playwright

    sessionid = settings.INSTAGRAM_SESSIONID.strip()
    clean_kw = re.sub(r"[#@]", "", keyword or "").strip()
    clean_tag = re.sub(r"[^a-zA-Z0-9_]", "", clean_kw)

    async with async_playwright() as p:
        browser = await launch_chromium(p)
        try:
            async def _run_pass(use_cookie: bool, target_urls: List[str], require_kw_filter: bool, max_wait_ms: int) -> List[Dict[str, Any]]:
                ctx = await browser.new_context(
                    user_agent=get_browser_ua(),
                    viewport={"width": 1280, "height": 900},
                    locale="id-ID",
                )
                gql_media: Dict[str, Dict[str, Any]] = {}
                candidate_links: List[Dict[str, str]] = []
                seen_codes: set = set()
                results_by_code: Dict[str, Dict[str, Any]] = {}

                try:
                    await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
                    if use_cookie and sessionid:
                        await ctx.add_cookies([{"name": "sessionid", "value": sessionid, "domain": ".instagram.com", "path": "/"}])

                    page = await ctx.new_page()

                    async def _abort_heavy(route):
                        if route.request.resource_type in ("image", "media", "font", "stylesheet"):
                            await route.abort()
                        else:
                            await route.continue_()

                    await page.route("**/*", _abort_heavy)

                    async def _on_resp(resp):
                        if "graphql" in resp.url and resp.status == 200:
                            try:
                                txt = await resp.text()
                                if "xdt_api__v1__feed__timeline__connection" in txt and "top_serp" not in txt:
                                    return
                                import json
                                data = json.loads(txt)
                                for item_dict in _extract_xdt_media_dicts(data):
                                    code = str(item_dict.get("code") or "").strip()
                                    if code and code not in gql_media:
                                        gql_media[code] = item_dict
                            except Exception:
                                pass

                    page.on("response", _on_resp)

                    for url in target_urls:
                        if len(gql_media) >= max_posts and len(candidate_links) >= max_posts:
                            break
                        try:
                            await page.goto(url, wait_until="domcontentloaded", timeout=18000)
                            await page.wait_for_timeout(750)
                            if _is_ig_gate_url(page.url):
                                print(
                                    f"[IG Playwright] {'Cookie sesi' if use_cookie else 'Akses anonim'} diarahkan ke {page.url.split('?')[0]}",
                                    flush=True,
                                )
                                break

                            try:
                                await page.wait_for_selector("a[href*='/p/'], a[href*='/reel/']", timeout=max_wait_ms)
                            except Exception:
                                pass

                            if len(gql_media) < max_posts:
                                await page.evaluate("window.scrollBy(0, 1200)")
                                await page.wait_for_timeout(1200)

                            anchors = await page.eval_on_selector_all(
                                "a[href*='/p/'], a[href*='/reel/']",
                                """els => els.map(e => {
                                    const img = e.querySelector('img');
                                    return {
                                        href: e.getAttribute('href') || '',
                                        alt: img ? (img.getAttribute('alt') || '') : '',
                                        src: img ? (img.getAttribute('src') || '') : ''
                                    };
                                })""",
                            )
                            for a in anchors:
                                href = a["href"]
                                m = re.search(r"/(p|reel)/([A-Za-z0-9_-]{6,20})/", href)
                                if not m:
                                    continue
                                kind, code = m.group(1), m.group(2)
                                if code in seen_codes:
                                    continue
                                seen_codes.add(code)
                                acc_m = re.match(r"^/([A-Za-z0-9_.]+)/(?:p|reel)/", href)
                                candidate_links.append({
                                    "code": code,
                                    "url": f"https://www.instagram.com/{kind}/{code}/",
                                    "owner": acc_m.group(1) if acc_m else "instagram",
                                    "alt": a["alt"],
                                    "thumb": a["src"],
                                })
                        except Exception as e:
                            print(f"[IG Playwright] URL {url} note: {e}", flush=True)

                    # 1. Harvest GraphQL XDTMediaDict items first (zero extra page navigation needed)
                    for code, m in gql_media.items():
                        item = _xdt_to_ig_item(m, keyword)
                        if not item:
                            continue
                        dt = datetime.fromisoformat(item["published_at"])
                        if not is_within_years(dt, year_range):
                            continue
                        if require_kw_filter and not matches_keyword(item["content"], keyword):
                            continue
                        if is_spam_or_judol(item["content"], item["title"], item["url"]):
                            continue
                        results_by_code[code] = item
                        if len(results_by_code) >= max_posts:
                            break

                    print(
                        f"[IG Playwright] auth={use_cookie} gql={len(gql_media)} dom={len(candidate_links)} harvested={len(results_by_code)}",
                        flush=True,
                    )

                    # 2. Visit remaining DOM post pages sequentially only if needed (low RAM for 2GB STB)
                    if len(results_by_code) < max_posts and candidate_links:
                        remaining = [c for c in candidate_links if c["code"] not in results_by_code]
                        if require_kw_filter:
                            # Round-robin across accounts so top posts from every media account get checked
                            by_owner: Dict[str, List[Dict[str, str]]] = {}
                            for c in remaining:
                                by_owner.setdefault(c["owner"], []).append(c)
                            interleaved: List[Dict[str, str]] = []
                            owner_queues = list(by_owner.values())
                            while any(owner_queues):
                                for q in owner_queues:
                                    if q:
                                        interleaved.append(q.pop(0))
                            remaining = interleaved
                        scan_limit = min(len(remaining), max_posts + 4 if not require_kw_filter else min(36, max_posts * 4))
                        deadline = time.monotonic() + 50.0
                        for cand in remaining[:scan_limit]:
                            if len(results_by_code) >= max_posts or time.monotonic() > deadline:
                                break
                            try:
                                await page.goto(cand["url"], wait_until="domcontentloaded", timeout=12000)
                                await page.wait_for_timeout(1200)
                                if _is_ig_gate_url(page.url):
                                    break
                                meta_map = await page.evaluate("""() => {
                                    const out = {};
                                    document.querySelectorAll('meta').forEach(m => {
                                        const k = m.getAttribute('property') || m.getAttribute('name');
                                        if (k) out[k] = m.getAttribute('content') || '';
                                    });
                                    return out;
                                }""")
                                og_desc = meta_map.get("og:description") or meta_map.get("description") or cand["alt"]
                                og_title = meta_map.get("og:title") or ""
                                og_img = meta_map.get("og:image") or cand["thumb"]
                                parsed = _parse_ig_og_description(og_desc)
                                caption = parsed["caption"] or cand["alt"]
                                if not is_within_years(parsed["dt"], year_range):
                                    continue
                                if require_kw_filter and not matches_keyword(f"{caption} {og_title}", keyword):
                                    continue
                                if is_spam_or_judol(caption, og_title, cand["url"]):
                                    continue

                                owner = parsed.get("author") or cand["owner"]
                                if owner == "instagram":
                                    m_owner = re.match(r"^([A-Za-z0-9_.]+)\s+(?:on|di)\s+Instagram", og_title, re.I)
                                    if m_owner and m_owner.group(1).lower() != "instagram":
                                        owner = m_owner.group(1)

                                results_by_code[cand["code"]] = _build_ig_item(
                                    code=cand["code"],
                                    owner=owner,
                                    caption=caption,
                                    keyword=keyword,
                                    post_url=cand["url"],
                                    thumbnail_url=og_img,
                                    dt=parsed["dt"],
                                    likes=parsed["likes"],
                                    comments=parsed["comments"],
                                )
                            except Exception:
                                continue

                    return list(results_by_code.values())[:max_posts]
                finally:
                    try:
                        await ctx.close()
                    except Exception:
                        pass

            # Pass 1: Authenticated keyword & hashtag search (if sessionid exists)
            items: List[Dict[str, Any]] = []
            if sessionid and (clean_kw or clean_tag):
                auth_urls: List[str] = []
                if clean_kw:
                    auth_urls.append(f"https://www.instagram.com/explore/search/keyword/?q={quote_plus(clean_kw)}")
                if clean_tag:
                    auth_urls.append(f"https://www.instagram.com/explore/tags/{clean_tag}/")
                items = await _run_pass(use_cookie=True, target_urls=auth_urls, require_kw_filter=False, max_wait_ms=9000)

            # Pass 2: Clean anonymous context on Indonesian public media IG accounts (avoids BadCookie redirects)
            if not items:
                if sessionid:
                    print("[IG Playwright] Beralih ke konteks anonim (tanpa cookie) pada akun media berita IG...", flush=True)
                profile_urls = [f"https://www.instagram.com/{acc}/" for acc in DEFAULT_IG_NEWS_ACCOUNTS]
                items = await _run_pass(use_cookie=False, target_urls=profile_urls, require_kw_filter=True, max_wait_ms=8000)

            return items
        finally:
            await browser.close()


def scrape_instagram(target_tag_or_profile: str = "karhutla", max_posts: int = 10, year_range: int = 5) -> List[Dict[str, Any]]:
    api_items = _try_instaloader_real(target_tag_or_profile, max_posts, year_range)
    if api_items:
        return api_items
    try:
        return run_coro_sync(_scrape_instagram_playwright(target_tag_or_profile, max_posts, year_range))
    except Exception as e:
        print(f"[IG Playwright] Note: {e}", flush=True)
        return []
