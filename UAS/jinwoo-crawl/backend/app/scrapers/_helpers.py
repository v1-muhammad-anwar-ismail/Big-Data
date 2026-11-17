"""Shared helpers for real-data scraping across JinwooCrawl scrapers."""
import asyncio
import concurrent.futures
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
UA_LINUX = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def get_browser_ua() -> str:
    """Match OS platform in UA string so ARM64 Linux Chrome does not trigger OS/UA mismatch anti-bot."""
    return UA_LINUX if os.name != "nt" else UA


def categorize_topic(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["hutan", "karhutla", "banjir", "gempa", "longsor", "bencana", "asap", "iklim", "hotspot", "cuaca", "bmkg", "bnpb"]):
        return "Disaster"
    if any(k in t for k in ["presiden", "wapres", "gibran", "prabowo", "menteri", "partai", "dpr", "pemilu", "pilkada", "politik", "kebijakan", "makar", "kpk"]):
        return "Politics"
    if any(k in t for k in ["saham", "rupiah", "inflasi", "ekonomi", "anggaran", "investasi", "keuangan", "pajak", "bisnis", "ekspor", "ihsg"]):
        return "Economy"
    if any(k in t for k in ["ai", "teknologi", "aplikasi", "cyber", "internet", "digital", "satelit", "data", "gadget"]):
        return "Tech"
    if any(k in t for k in ["viral", "kasus", "polisi", "sidang", "hukum", "sosial", "masyarakat", "warga", "netizen", "publik"]):
        return "Social"
    return "News"


_NEG_WORDS = {
    "kebakaran", "karhutla", "asap", "bencana", "korban", "meninggal", "tewas", "rusak",
    "banjir", "gempa", "dugaan", "kasus", "krisis", "bahaya", "parah", "darurat",
    "protes", "tolak", "kecam", "pelanggaran", "buruk", "terbakar", "ispa", "macet",
}
_POS_WORDS = {
    "berhasil", "padam", "pulih", "bantuan", "aman", "sehat", "dukung", "kolaborasi",
    "apresiasi", "penghargaan", "inovasi", "solusi", "maju", "baik", "damai", "sukses",
}


def estimate_tone(text: str) -> float:
    words = re.findall(r"[a-z]+", (text or "").lower())
    if not words:
        return 0.0
    neg = sum(1 for w in words if w in _NEG_WORDS)
    pos = sum(1 for w in words if w in _POS_WORDS)
    score = (pos - neg) * 0.6
    return round(max(-5.0, min(5.0, score)), 2)


def is_within_years(dt: datetime, year_range: int) -> bool:
    if not dt:
        return True
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    cutoff_year = max(2015, now.year - max(1, int(year_range)))
    return dt.year >= cutoff_year


def keyword_tokens(keyword: str) -> List[str]:
    clean = re.sub(r"[#@]", " ", (keyword or "").lower()).strip()
    tokens = [t for t in clean.split() if len(t) >= 2]
    return tokens or ([clean] if clean else [])


def matches_keyword(text: str, keyword: str) -> bool:
    if not keyword or not keyword.strip():
        return True
    low = (text or "").lower()
    clean = re.sub(r"[#@]", "", keyword.lower()).strip()
    if clean in low:
        return True
    toks = keyword_tokens(keyword)
    return len(toks) > 1 and all(t in low for t in toks)


def make_doc_id(prefix: str, unique_key: str) -> str:
    return hashlib.md5(f"{prefix}_{unique_key}".encode("utf-8", errors="ignore")).hexdigest()


_DROP_QUERY_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "igshid", "ref", "s", "si", "t", "r",
    "sender_device", "is_from_webapp", "web_id",
}


def canonicalize_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        sp = urlsplit(raw)
        scheme = (sp.scheme or "https").lower()
        netloc = sp.netloc.lower()
        if netloc.startswith("www."):
            netloc_norm = netloc
        else:
            netloc_norm = netloc
        path = sp.path.rstrip("/") or "/"
        kept_qs = [(k, v) for k, v in parse_qsl(sp.query, keep_blank_values=False) if k.lower() not in _DROP_QUERY_PARAMS]
        kept_qs.sort()
        query = urlencode(kept_qs)
        return urlunsplit((scheme, netloc_norm, path, query, ""))
    except Exception:
        return raw.split("#")[0].rstrip("/").lower()


def compute_content_hash(item: Dict[str, Any]) -> str:
    title = (item.get("title") or "").strip()
    title = re.sub(r"^(?:TikTok API|TikTok|Pyktok|Instagram)\s+", "", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip().lower()
    content = re.sub(r"\s+", " ", (item.get("content") or "")).strip().lower()[:180]
    author = re.sub(r"\s+", " ", (item.get("author_or_source") or "")).strip().lower()
    raw_key = f"{author}|{title}|{content}"
    return hashlib.md5(raw_key.encode("utf-8", errors="ignore")).hexdigest()


_JUDOL_EXACT_RE = re.compile(
    r"\{\{[^}]+\}\}|"
    r"\b(?:otot133|slot88|slot777|zeus138|bet88|sbobet|maxwin|rtp\s*live|"
    r"slot\s*gacor|situs\s*slot|link\s*gacor|pola\s*gacor|daftar\s*slot|"
    r"agen\s*togel|bandar\s*togel|toto\s*macau|scatter\s*hitam|bonus\s*new\s*member|"
    r"mahjong\s*ways|gates\s*of\s*olympus|pragmatic\s*play|deposit\s*pulsa|"
    r"kemenangan\s*di\s*bayar\s*tuntas|kemenangan\s*dibayar\s*tuntas)\b",
    re.I,
)


def is_spam_or_judol(text: str, title: str = "", url: str = "") -> bool:
    combined = f"{title} {text} {url}"
    if not combined.strip():
        return False
    # Strip invisible zero-width unicode obfuscators used by YouTube/TikTok judol comment bots
    cleaned = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", combined)
    if _JUDOL_EXACT_RE.search(cleaned):
        return True
    low = cleaned.lower()
    if "{{" in low and "}}" in low:
        return True
    if any(w in low for w in ("gacor", "slot", "togel", "casino", "judol", "wd ")) and any(
        p in low for p in ("main disini", "main di sini", "daftar", "depo", "withdraw", "link bio", "klik bio", "wa.me/", "t.me/", "bit.ly/", "menang 100%", "100% kemenangan")
    ):
        return True
    return False


def run_coro_sync(coro):
    """Run an async coroutine safely even inside an active event loop thread."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def ensure_runtime_tmpdir() -> str:
    """Ensure TMPDIR points to a real existing directory so Playwright mkdtemp never hits ENOENT."""
    cur = os.environ.get("TMPDIR", "").strip()
    if cur and os.path.isdir(cur):
        return cur
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    safe_tmp = os.path.join(base_dir, ".pw-tmp")
    try:
        os.makedirs(safe_tmp, exist_ok=True)
    except Exception:
        safe_tmp = "/tmp" if os.name != "nt" else os.environ.get("TEMP", ".")
    os.environ["TMPDIR"] = os.environ["TEMP"] = os.environ["TMP"] = safe_tmp
    return safe_tmp


ensure_runtime_tmpdir()


async def launch_chromium(playwright_obj):
    """Launch headless Chromium cleanly on both desktop and low-RAM ARM Linux STB."""
    ensure_runtime_tmpdir()
    args = ["--disable-blink-features=AutomationControlled"]
    if os.name != "nt":
        args.extend(["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    launch_kwargs: Dict[str, Any] = {"headless": True, "args": args}

    custom_exec = os.getenv("CHROMIUM_EXECUTABLE_PATH", "").strip()
    if custom_exec and os.path.exists(custom_exec):
        return await playwright_obj.chromium.launch(executable_path=custom_exec, **launch_kwargs)

    try:
        return await playwright_obj.chromium.launch(**launch_kwargs)
    except Exception:
        if os.name != "nt":
            for candidate in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"):
                if os.path.exists(candidate):
                    return await playwright_obj.chromium.launch(executable_path=candidate, **launch_kwargs)
        raise


async def fetch_tiktok_search_via_playwright(
    queries: List[str],
    session_key: str = "",
    ms_token: str = "",
    max_records: int = 20,
    year_range: int = 5,
    extra_browser_cookies: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, Any]]:
    """Use Playwright Chromium to capture real TikTok /api/search/general/full/ payloads."""
    from playwright.async_api import async_playwright

    captured: Dict[str, Dict[str, Any]] = {}
    deadline = time.monotonic() + 65.0
    async with async_playwright() as p:
        browser = await launch_chromium(p)
        try:
            async def _run_pass(use_auth_cookies: bool) -> None:
                ctx = await browser.new_context(
                    user_agent=get_browser_ua(),
                    viewport={"width": 1280, "height": 900},
                    locale="id-ID",
                )
                await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
                cookies = []
                if use_auth_cookies:
                    if session_key:
                        cookies.append({"name": "sessionid", "value": session_key, "domain": ".tiktok.com", "path": "/"})
                    if ms_token:
                        cookies.append({"name": "msToken", "value": ms_token, "domain": ".tiktok.com", "path": "/"})
                if extra_browser_cookies:
                    cookies.extend(extra_browser_cookies)
                if cookies:
                    await ctx.add_cookies(cookies)

                page = await ctx.new_page()

                async def _abort_heavy(route):
                    if route.request.resource_type in ("image", "media", "font"):
                        await route.abort()
                    else:
                        await route.continue_()

                await page.route("**/*", _abort_heavy)

                async def on_resp(resp):
                    if any(ep in resp.url for ep in ("/api/search/general/full/", "/api/search/item/full/", "/api/challenge/item_list/")):
                        try:
                            txt = await resp.text()
                            if not txt or "{" not in txt:
                                return
                            data = json.loads(txt)
                            for entry in data.get("data", []):
                                it = entry.get("item")
                                if isinstance(it, dict) and it.get("id"):
                                    captured[str(it["id"])] = it
                            for key_list in ("item_list", "itemList"):
                                for it in data.get(key_list, []):
                                    if isinstance(it, dict) and it.get("id"):
                                        captured[str(it["id"])] = it
                        except Exception:
                            pass

                page.on("response", on_resp)

                async def _extract_dom(query_hint: str) -> None:
                    try:
                        dom_items = await page.evaluate("""() => {
                            const out = [];
                            document.querySelectorAll("a[href*='/video/']").forEach(a => {
                                const href = a.getAttribute('href') || '';
                                const m = href.match(/@([A-Za-z0-9_.]+)\\/video\\/(\\d+)/);
                                if (!m) return;
                                const img = a.querySelector('img');
                                const text = (img && img.getAttribute('alt')) || a.textContent || '';
                                out.push({ id: m[2], author: m[1], desc: text.trim(), cover: img ? (img.getAttribute('src') || '') : '' });
                            });
                            return out;
                        }""")
                        for d_it in dom_items:
                            vid = str(d_it.get("id") or "")
                            if vid and vid not in captured:
                                captured[vid] = {
                                    "id": vid,
                                    "desc": d_it.get("desc") or query_hint,
                                    "author": {"uniqueId": d_it.get("author") or "tiktok_user", "nickname": d_it.get("author") or "tiktok_user"},
                                    "video": {"cover": d_it.get("cover") or ""},
                                    "stats": {},
                                }
                    except Exception:
                        pass

                first_slug = re.sub(r"[^a-zA-Z0-9_]", "", queries[0]) or "berita"
                try:
                    await page.goto(f"https://www.tiktok.com/tag/{first_slug}", wait_until="domcontentloaded", timeout=15000)
                    try:
                        await page.wait_for_selector("a[href*='/video/']", timeout=6000)
                    except Exception:
                        await page.wait_for_timeout(2000)
                    await _extract_dom(queries[0])
                except Exception:
                    pass

                from urllib.parse import quote
                for idx, q in enumerate(queries[:3]):
                    if len(captured) >= max_records or time.monotonic() > deadline:
                        break
                    # Stop trying extra queries inside poisoned session if first search yielded 0 so anonymous fallback runs
                    if use_auth_cookies and idx >= 1 and not captured:
                        break
                    url = f"https://www.tiktok.com/search?q={quote(q)}"
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=18000)
                        try:
                            await page.wait_for_selector("a[href*='/video/']", timeout=7000)
                        except Exception:
                            await page.wait_for_timeout(2500)
                        if len(captured) < max_records and time.monotonic() < deadline:
                            await page.evaluate("window.scrollBy(0, 2200)")
                            await page.wait_for_timeout(2000)
                        if not captured:
                            await _extract_dom(q)
                        title_dbg = ""
                        if not captured:
                            try:
                                title_dbg = f" (title={await page.title()!r})"
                            except Exception:
                                pass
                        print(f"[TikTok PW] auth={use_auth_cookies} query='{q}' -> captured={len(captured)}{title_dbg}", flush=True)
                    except Exception as exc:
                        print(f"[TikTok PW] Query '{q}' timeout/note: {exc}", flush=True)
                        continue

                await ctx.close()

            await _run_pass(use_auth_cookies=bool(session_key or ms_token))
            if not captured and (session_key or ms_token) and time.monotonic() < deadline - 10:
                print("[TikTok PW] Cookie sesi tidak mengembalikan data di IP ini, mencoba mode publik anonim...", flush=True)
                await _run_pass(use_auth_cookies=False)
        finally:
            await browser.close()

    # Filter by year_range and convert raw dicts consistently
    out: List[Dict[str, Any]] = []
    for vid_id, it in captured.items():
        ctime = int(it.get("createTime") or 0)
        dt = datetime.fromtimestamp(ctime, tz=timezone.utc) if ctime else datetime.now(timezone.utc)
        if not is_within_years(dt, year_range):
            continue
        out.append(it)
        if len(out) >= max_records:
            break
    return out


def normalize_tiktok_item(
    it: Dict[str, Any],
    tool_source: str,
    keyword: str,
    title_prefix: str = "TikTok",
) -> Dict[str, Any]:
    vid_id = str(it.get("id", ""))
    desc = (it.get("desc") or "").strip()
    author_obj = it.get("author") or {}
    author = author_obj.get("uniqueId") or "tiktok_user"
    nickname = author_obj.get("nickname") or author
    stats = it.get("stats") or {}
    video_obj = it.get("video") or {}
    cover = video_obj.get("cover") or video_obj.get("originCover") or video_obj.get("dynamicCover") or ""
    ctime = int(it.get("createTime") or 0)
    dt = datetime.fromtimestamp(ctime, tz=timezone.utc) if ctime else datetime.now(timezone.utc)
    cat = categorize_topic(desc or keyword)
    headline = desc[:90] + ("..." if len(desc) > 90 else "") if desc else f"Video #{keyword} oleh @{author}"

    return {
        "id": make_doc_id(tool_source, vid_id),
        "tool_source": tool_source,
        "platform": "TikTok",
        "keyword": keyword,
        "category": cat,
        "title": f"{title_prefix} @{author}: {headline}",
        "content": desc or f"Video TikTok oleh @{author} ({nickname}) terkait topik {keyword}.",
        "url": f"https://www.tiktok.com/@{author}/video/{vid_id}",
        "thumbnail_url": cover,
        "author_or_source": f"@{author} ({nickname})" if nickname != author else f"@{author}",
        "published_at": dt.isoformat(),
        "published_date": dt.strftime("%Y-%m-%d"),
        "metrics": {
            "views": int(stats.get("playCount") or 0),
            "likes": int(stats.get("diggCount") or 0),
            "comments": int(stats.get("commentCount") or 0),
            "shares": int(stats.get("shareCount") or 0),
            "sentiment_tone": estimate_tone(desc),
        },
        "raw_data": {
            "video_id": vid_id,
            "author_id": author_obj.get("id"),
            "duration": video_obj.get("duration"),
            "stats": stats,
        },
    }
