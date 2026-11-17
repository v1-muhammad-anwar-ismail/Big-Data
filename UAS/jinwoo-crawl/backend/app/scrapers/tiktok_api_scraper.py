"""Real TikTok scraper powered by davidteather/TikTok-Api + Playwright session fallback (zero mock data)."""
import asyncio
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List
from app.config import settings
from app.scrapers._helpers import (
    fetch_tiktok_search_via_playwright,
    is_within_years,
    normalize_tiktok_item,
    run_coro_sync,
)


def scrape_tiktok_api(keyword: str = "karhutla", max_records: int = 10, year_range: int = 5) -> List[Dict[str, Any]]:
    clean_kw = re.sub(r"[#@]", "", keyword or "").strip()
    if not clean_kw:
        return []

    session_key = settings.TIKTOK_SESSION_KEY.strip()
    ms_token = getattr(settings, "TIKTOK_MS_TOKEN", "").strip()
    collected: Dict[str, Dict[str, Any]] = {}

    async def _try_native_ttapi() -> None:
        from TikTokApi import TikTokApi

        slug = re.sub(r"[^a-zA-Z0-9_]", "", clean_kw)
        if not slug:
            return
        async with TikTokApi() as api:
            try:
                cookies = {"sessionid": session_key} if session_key else None
                browser_args = ["--disable-blink-features=AutomationControlled"]
                if os.name != "nt":
                    browser_args.extend(["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
                await asyncio.wait_for(
                    api.create_sessions(
                        num_sessions=1,
                        headless=True,
                        starting_url="https://www.tiktok.com/404",
                        suppress_resource_load_types=["image", "media", "font", "stylesheet"],
                        override_browser_args=browser_args,
                        ms_tokens=[ms_token] if ms_token else None,
                        cookies=[cookies] if cookies else None,
                        timeout=10000,
                        sleep_after=1,
                        browser="chromium",
                    ),
                    timeout=14.0,
                )
                async for video in api.hashtag(name=slug).videos(count=min(max_records, 25)):
                    d = video.as_dict
                    if isinstance(d, dict) and d.get("id"):
                        collected[str(d["id"])] = d
                    if len(collected) >= max_records:
                        break
            finally:
                try:
                    await api.close_sessions()
                except Exception:
                    pass

    try:
        run_coro_sync(_try_native_ttapi())
    except Exception as e:
        print(f"[TikTokApi] Hashtag API skipped/blocked ({type(e).__name__}), using Playwright fallback...", flush=True)

    # Real Playwright search fallback (captures real search/tag payloads, never mock data)
    if len(collected) < max_records:
        try:
            raw_items = run_coro_sync(
                fetch_tiktok_search_via_playwright(
                    queries=[f"{clean_kw} terbaru", f"{clean_kw} fakta", f"{clean_kw} viral"],
                    session_key=session_key,
                    ms_token=ms_token,
                    max_records=max_records - len(collected),
                    year_range=year_range,
                )
            )
            for it in raw_items:
                if it.get("id"):
                    collected[str(it["id"])] = it
        except Exception as e:
            print(f"[TikTokApi] Playwright fallback note: {e}", flush=True)

    results: List[Dict[str, Any]] = []
    for it in collected.values():
        ctime = int(it.get("createTime") or 0)
        dt = datetime.fromtimestamp(ctime, tz=timezone.utc) if ctime else datetime.now(timezone.utc)
        if not is_within_years(dt, year_range):
            continue
        results.append(normalize_tiktok_item(it, tool_source="tiktok_api", keyword=keyword, title_prefix="TikTok API"))
        if len(results) >= max_records:
            break
    return results
