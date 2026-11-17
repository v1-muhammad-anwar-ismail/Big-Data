"""Real academic TikTok scraper (Universal Rehydration JSON + Playwright session discovery, zero heavy bloat)."""
import json
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from app.config import settings
from app.scrapers._helpers import (
    UA,
    fetch_tiktok_search_via_playwright,
    normalize_tiktok_item,
    run_coro_sync,
)


def _fetch_tiktok_universal_json(url: str, cookies: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """Lightweight replacement for pyktok.alt_get_tiktok_json without streamlit/pandas/browser_cookie3 bloat."""
    try:
        r = requests.get(
            url,
            headers={"User-Agent": UA, "Referer": "https://www.tiktok.com/"},
            cookies=cookies or None,
            timeout=(5, 10),
        )
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        script_el = soup.find("script", attrs={"id": "__UNIVERSAL_DATA_FOR_REHYDRATION__"})
        if script_el and script_el.string:
            return json.loads(script_el.string)
    except Exception:
        pass
    return None


def scrape_pyktok(
    keyword: str = "karhutla",
    video_urls: List[str] = None,
    max_records: int = 10,
    year_range: int = 5,
) -> List[Dict[str, Any]]:
    clean_kw = keyword.replace("#", "").strip()
    candidates: List[Dict[str, Any]] = []
    target_urls: List[str] = list(video_urls or [])
    session_key = settings.TIKTOK_SESSION_KEY.strip()
    ms_token = getattr(settings, "TIKTOK_MS_TOKEN", "").strip()

    if not target_urls and clean_kw:
        candidates = run_coro_sync(
            fetch_tiktok_search_via_playwright(
                queries=[f"{clean_kw} opini", f"{clean_kw} update", f"{clean_kw} analisis", f"{clean_kw} fakta"],
                session_key=session_key,
                ms_token=ms_token,
                max_records=max_records,
                year_range=year_range,
            )
        )
        for it in candidates:
            author = (it.get("author") or {}).get("uniqueId")
            vid = it.get("id")
            if author and vid:
                target_urls.append(f"https://www.tiktok.com/@{author}/video/{vid}")

    candidate_by_id = {str(it.get("id")): it for it in candidates if it.get("id")}
    req_cookies: Dict[str, str] = {}
    if session_key:
        req_cookies["sessionid"] = session_key
    if ms_token:
        req_cookies["msToken"] = ms_token

    results: List[Dict[str, Any]] = []
    seen_ids: set = set()

    for url in target_urls[:max_records]:
        enriched_item = None
        try:
            meta = _fetch_tiktok_universal_json(url, cookies=req_cookies)
            if isinstance(meta, dict):
                scope = meta.get("__DEFAULT_SCOPE__", {})
                struct = (
                    scope.get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct")
                    or meta.get("itemInfo", {}).get("itemStruct")
                )
                if isinstance(struct, dict) and struct.get("id"):
                    enriched_item = struct
        except Exception as e:
            print(f"[Pyktok] metadata note for {url}: {e}", flush=True)

        if not enriched_item:
            vid_from_url = url.rstrip("/").split("/")[-1].split("?")[0]
            enriched_item = candidate_by_id.get(vid_from_url)

        if not enriched_item or str(enriched_item.get("id")) in seen_ids:
            continue
        seen_ids.add(str(enriched_item["id"]))

        doc = normalize_tiktok_item(
            enriched_item,
            tool_source="pyktok",
            keyword=keyword,
            title_prefix="Pyktok",
        )
        stats = enriched_item.get("stats") or {}
        if stats.get("collectCount") is not None:
            doc["raw_data"]["collect_count"] = stats.get("collectCount")
        doc["raw_data"]["extracted_by"] = "tiktok_rehydration_json"
        results.append(doc)

    return results
