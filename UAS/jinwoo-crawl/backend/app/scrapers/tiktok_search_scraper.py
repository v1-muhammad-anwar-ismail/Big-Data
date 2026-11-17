"""Real TikTok Web Search scraper via Playwright intercepting TikTok /api/search/general/full/."""
from typing import Any, Dict, List
from app.config import settings
from app.scrapers._helpers import (
    fetch_tiktok_search_via_playwright,
    normalize_tiktok_item,
    run_coro_sync,
)


def scrape_tiktok_search(keyword: str = "karhutla", max_records: int = 15, year_range: int = 5) -> List[Dict[str, Any]]:
    clean_kw = keyword.replace("#", "").strip()
    if not clean_kw:
        return []

    session_key = settings.TIKTOK_SESSION_KEY.strip()
    ms_token = getattr(settings, "TIKTOK_MS_TOKEN", "").strip()
    queries = [
        clean_kw,
        f"{clean_kw} berita",
        f"{clean_kw} indonesia",
        f"{clean_kw} hari ini",
        f"{clean_kw} kompas",
    ]

    raw_items = run_coro_sync(
        fetch_tiktok_search_via_playwright(
            queries=queries,
            session_key=session_key,
            ms_token=ms_token,
            max_records=max_records,
            year_range=year_range,
        )
    )

    return [
        normalize_tiktok_item(it, tool_source="tiktok_search", keyword=keyword, title_prefix="TikTok")
        for it in raw_items[:max_records]
    ]
