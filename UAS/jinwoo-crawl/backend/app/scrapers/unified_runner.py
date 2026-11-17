from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.database import save_scraped_items
from app.scrapers.gdelt_scraper import scrape_gdelt
from app.scrapers.tiktok_search_scraper import scrape_tiktok_search
from app.scrapers.pyktok_scraper import scrape_pyktok
from app.scrapers.facebook_scraper import scrape_facebook_pages
from app.scrapers.instagram_scraper import scrape_instagram
from app.scrapers.tiktok_api_scraper import scrape_tiktok_api
from app.scrapers.youtube_scraper import scrape_youtube_api
from app.scrapers.meta_ad_scraper import scrape_meta_ads

SCRAPER_DISPATCHER = {
    "gdelt": lambda kw, count: scrape_gdelt(keyword=kw, max_records=count),
    "tiktok_search": lambda kw, count: scrape_tiktok_search(keyword=kw, max_records=count),
    "pyktok": lambda kw, count: scrape_pyktok(keyword=kw, max_records=count),
    "facebook_pages": lambda kw, count: scrape_facebook_pages(page_name="detikcom", keyword=kw, max_posts=count),
    "instaloader": lambda kw, count: scrape_instagram(target_tag_or_profile=kw, max_posts=count),
    "tiktok_api": lambda kw, count: scrape_tiktok_api(keyword=kw, max_records=count),
    "youtube_api": lambda kw, count: scrape_youtube_api(keyword=kw, max_results=count),
    "meta_ad_library": lambda kw, count: scrape_meta_ads(keyword=kw, max_records=count),
}

def run_single_scraper(tool_name: str, keyword: str, count: int = 10, save_to_db: bool = True) -> Dict[str, Any]:
    if tool_name not in SCRAPER_DISPATCHER:
        return {"tool": tool_name, "status": "error", "message": f"Tool '{tool_name}' tidak dikenal", "items": []}

    try:
        fn = SCRAPER_DISPATCHER[tool_name]
        items = fn(keyword, count)
        inserted_count = 0
        if save_to_db and items:
            save_result = save_scraped_items(items)
            inserted_count = save_result.get("inserted_count", 0)

        return {
            "tool": tool_name,
            "status": "success",
            "keyword": keyword,
            "count": len(items),
            "inserted_to_db": inserted_count,
            "items": items
        }
    except Exception as e:
        return {
            "tool": tool_name,
            "status": "error",
            "message": str(e),
            "items": []
        }

def run_all_scrapers(keyword: str, count_per_tool: int = 8, save_to_db: bool = True) -> Dict[str, Any]:
    """Menjalankan seluruh 8 Tool & API Scraping secara paralel (multithreading)"""
    all_results: Dict[str, Any] = {}
    combined_items: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_tool = {
            executor.submit(run_single_scraper, tool_name, keyword, count_per_tool, False): tool_name
            for tool_name in SCRAPER_DISPATCHER.keys()
        }

        for future in as_completed(future_to_tool):
            tool = future_to_tool[future]
            try:
                res = future.result()
                all_results[tool] = res
                combined_items.extend(res.get("items", []))
            except Exception as e:
                all_results[tool] = {"tool": tool, "status": "error", "message": str(e), "items": []}

    inserted_total = 0
    if save_to_db and combined_items:
        save_res = save_scraped_items(combined_items)
        inserted_total = save_res.get("inserted_count", 0)

    return {
        "status": "success",
        "keyword": keyword,
        "total_items": len(combined_items),
        "total_saved_to_db": inserted_total,
        "details_by_tool": all_results
    }
