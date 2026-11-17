import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.database import get_existing_identity_maps, save_scraped_items
from app.scrapers._helpers import canonicalize_url, compute_content_hash, is_spam_or_judol
from app.scrapers.gdelt_scraper import scrape_gdelt
from app.scrapers.tiktok_search_scraper import scrape_tiktok_search
from app.scrapers.pyktok_scraper import scrape_pyktok
from app.scrapers.facebook_scraper import scrape_facebook_pages
from app.scrapers.instagram_scraper import scrape_instagram
from app.scrapers.tiktok_api_scraper import scrape_tiktok_api
from app.scrapers.youtube_scraper import scrape_youtube_api

SCRAPER_DISPATCHER = {
    "gdelt": lambda kw, count, yr: scrape_gdelt(keyword=kw, max_records=count, timespan=f"{yr}y"),
    "tiktok_search": lambda kw, count, yr: scrape_tiktok_search(keyword=kw, max_records=count, year_range=yr),
    "pyktok": lambda kw, count, yr: scrape_pyktok(keyword=kw, max_records=count, year_range=yr),
    "facebook_pages": lambda kw, count, yr: scrape_facebook_pages(page_name="detikcom", keyword=kw, max_posts=count, year_range=yr),
    "instaloader": lambda kw, count, yr: scrape_instagram(target_tag_or_profile=kw, max_posts=count, year_range=yr),
    "tiktok_api": lambda kw, count, yr: scrape_tiktok_api(keyword=kw, max_records=count, year_range=yr),
    "youtube_api": lambda kw, count, yr: scrape_youtube_api(keyword=kw, max_results=count, year_range=yr),
}


def _dedup_and_clean_items(tool_name: str, items: List[Dict[str, Any]], check_db: bool = True) -> List[Dict[str, Any]]:
    existing_urls: Dict[str, str] = {}
    existing_hashes: Dict[str, str] = {}
    if check_db:
        try:
            existing_urls, existing_hashes = get_existing_identity_maps()
        except Exception:
            pass

    cleaned: List[Dict[str, Any]] = []
    batch_urls: set = set()
    batch_hashes: set = set()
    for it in items:
        if is_spam_or_judol(it.get("content", ""), it.get("title", ""), it.get("url", "")):
            continue
        doc_id = str(it.get("id") or "")
        cu = canonicalize_url(it.get("url", ""))
        ch = compute_content_hash(it)
        if cu and (cu in batch_urls or (cu in existing_urls and existing_urls[cu] != doc_id)):
            continue
        if ch and (ch in batch_hashes or (ch in existing_hashes and existing_hashes[ch] != doc_id)):
            continue
        if cu:
            batch_urls.add(cu)
        if ch:
            batch_hashes.add(ch)
        cleaned.append(it)
    return cleaned

def run_single_scraper(tool_name: str, keyword: str, count: int = 10, year_range: int = 5, save_to_db: bool = True) -> Dict[str, Any]:
    if tool_name not in SCRAPER_DISPATCHER:
        return {"tool": tool_name, "status": "error", "message": f"Tool '{tool_name}' tidak dikenal", "items": []}

    t0 = time.time()
    print(f"[JinwooCrawl] -> Memulai {tool_name} | keyword='{keyword}' | target={count} | rentang={year_range}y", flush=True)
    try:
        fn = SCRAPER_DISPATCHER[tool_name]
        raw_items = fn(keyword, count, year_range)
        items = _dedup_and_clean_items(tool_name, raw_items, check_db=save_to_db)
        inserted_count = 0
        if save_to_db and items:
            save_result = save_scraped_items(items)
            inserted_count = save_result.get("inserted_count", 0)

        print(
            f"[JinwooCrawl] <- Selesai {tool_name}: {len(items)} unik (dari {len(raw_items)} mentah) ({time.time() - t0:.1f}s)",
            flush=True,
        )
        return {
            "tool": tool_name,
            "status": "success" if items else "empty",
            "keyword": keyword,
            "year_range": year_range,
            "count": len(items),
            "inserted_to_db": inserted_count,
            "message": "" if items else f"Tidak ada postingan unik baru untuk '{keyword}' pada sumber {tool_name}.",
            "items": items
        }
    except Exception as e:
        print(f"[JinwooCrawl] !! Error {tool_name}: {e}", flush=True)
        return {
            "tool": tool_name,
            "status": "error",
            "count": 0,
            "message": str(e),
            "items": []
        }

def run_selected_scrapers(
    tool_names: List[str],
    keyword: str,
    count_per_tool: int = 10,
    year_range: int = 5,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """Menjalankan daftar tool yang dipilih secara paralel dengan filter rentang tahun (1-5 tahun terakhir)"""
    valid_tools = [t for t in tool_names if t in SCRAPER_DISPATCHER]
    if not valid_tools:
        valid_tools = list(SCRAPER_DISPATCHER.keys())

    all_results: Dict[str, Any] = {}
    combined_items: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=min(len(valid_tools), 8)) as executor:
        future_to_tool = {
            executor.submit(run_single_scraper, tool_name, keyword, count_per_tool, year_range, False): tool_name
            for tool_name in valid_tools
        }

        for future in as_completed(future_to_tool):
            tool = future_to_tool[future]
            try:
                res = future.result()
                all_results[tool] = res
                combined_items.extend(res.get("items", []))
            except Exception as e:
                all_results[tool] = {"tool": tool, "status": "error", "message": str(e), "items": []}

    combined_items = _dedup_and_clean_items("combined", combined_items, check_db=save_to_db)
    inserted_total = 0
    if save_to_db and combined_items:
        save_res = save_scraped_items(combined_items)
        inserted_total = save_res.get("inserted_count", 0)

    return {
        "status": "success",
        "keyword": keyword,
        "year_range": year_range,
        "selected_tools": valid_tools,
        "total_items": len(combined_items),
        "total_saved_to_db": inserted_total,
        "details_by_tool": all_results
    }

def run_all_scrapers(keyword: str, count_per_tool: int = 8, year_range: int = 5, save_to_db: bool = True) -> Dict[str, Any]:
    """Menjalankan seluruh 7 Tool & API Scraping secara paralel dengan filter rentang tahun"""
    return run_selected_scrapers(
        tool_names=list(SCRAPER_DISPATCHER.keys()),
        keyword=keyword,
        count_per_tool=count_per_tool,
        year_range=year_range,
        save_to_db=save_to_db
    )
