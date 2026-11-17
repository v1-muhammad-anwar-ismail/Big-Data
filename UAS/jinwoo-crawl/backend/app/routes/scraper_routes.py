from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.config import settings
from app.scrapers.unified_runner import run_single_scraper, run_all_scrapers, SCRAPER_DISPATCHER
from app.scrapers.gdelt_scraper import get_gdelt_timeline_data

router = APIRouter(prefix="/api/scrape", tags=["Scraping Controls"])

class SingleScrapeRequest(BaseModel):
    tool: str = Field(..., description="Nama tool (gdelt, tiktok_search, pyktok, facebook_pages, instaloader, tiktok_api, youtube_api, meta_ad_library)")
    keyword: str = Field("karhutla", description="Kata kunci isu/topik")
    count: int = Field(10, ge=1, le=100, description="Jumlah target data")
    save_to_db: bool = Field(True, description="Apakah hasil disimpan ke MongoDB")

class AllScrapeRequest(BaseModel):
    keyword: str = Field("karhutla", description="Kata kunci isu/topik untuk semua 8 tools")
    count_per_tool: int = Field(8, ge=1, le=50, description="Jumlah data per tool")
    save_to_db: bool = Field(True, description="Apakah hasil disimpan ke MongoDB")

@router.get("/tools")
def list_available_tools() -> Dict[str, Any]:
    """Menampilkan status konfigurasi dan ketersediaan seluruh 8 Tool & API Scraping"""
    return {
        "total_tools": 8,
        "tools": [
            {
                "id": "gdelt",
                "name": "GDELT 2.0 Doc API",
                "platform": "Global News Media",
                "type": "Free Official API",
                "auth_required": False,
                "auth_status": "Ready (No key needed)",
                "description": "Memantau berita global & nasional Indonesia secara real-time dengan metadata tone dan timeline volume."
            },
            {
                "id": "tiktok_search",
                "name": "TikTok Web Search Scraper",
                "platform": "TikTok",
                "type": "Open-Source Scraper",
                "auth_required": False,
                "auth_status": "Ready (Anonymous)",
                "description": "Scraping video TikTok publik berdasarkan kata kunci atau tagar tanpa memerlukan login."
            },
            {
                "id": "pyktok",
                "name": "dfreelon/pyktok",
                "platform": "TikTok",
                "type": "Academic Research Package",
                "auth_required": False,
                "auth_status": "Ready",
                "description": "Library penelitian ilmiah media sosial untuk ekstraksi metadata mendalam video TikTok."
            },
            {
                "id": "facebook_pages",
                "name": "Facebook Pages Scraper",
                "platform": "Facebook",
                "type": "Public Parser",
                "auth_required": False,
                "auth_status": "Ready (Public Fanpages)",
                "description": "Mengekstrak postingan dari Fanpage berita publik (Detikcom, Kompas, CNN) tanpa browser overhead."
            },
            {
                "id": "instaloader",
                "name": "Instaloader Instagram",
                "platform": "Instagram",
                "type": "Python Library + Dummy Auth",
                "auth_required": True,
                "auth_status": "Configured via .env" if settings.INSTAGRAM_USERNAME else "Anonymous Mode (Public Profiles)",
                "description": "Scraping postingan Instagram akun media massa dengan dukungan akun dummy dinamis dari .env."
            },
            {
                "id": "tiktok_api",
                "name": "davidteather/TikTok-Api",
                "platform": "TikTok",
                "type": "Session-Based API Wrapper",
                "auth_required": True,
                "auth_status": "Session Key Active" if settings.TIKTOK_SESSION_KEY else "Default Public Session",
                "description": "API wrapper populer untuk mengambil video dan statistik tagar dengan session key dinamis."
            },
            {
                "id": "youtube_api",
                "name": "YouTube Data API v3",
                "platform": "YouTube",
                "type": "Google Cloud API",
                "auth_required": True,
                "auth_status": "Google API Key Active" if settings.YOUTUBE_API_KEY else "Public Media RSS Mode",
                "description": "Mengambil siaran berita TV (CNN Indonesia, KompasTV, dll) beserta metrik views dan komentar."
            },
            {
                "id": "meta_ad_library",
                "name": "Meta Ad Library API",
                "platform": "Meta Ads (FB & IG)",
                "type": "Meta Official Graph API",
                "auth_required": True,
                "auth_status": "Meta Token Active" if settings.META_ACCESS_TOKEN else "Issue Advocacy Sandbox Mode",
                "description": "Melacak transparansi iklan isu politik, sosial, dan advokasi lingkungan di wilayah Indonesia."
            }
        ]
    }

@router.post("/single")
def trigger_single_scrape(req: SingleScrapeRequest):
    if req.tool not in SCRAPER_DISPATCHER:
        raise HTTPException(status_code=400, detail=f"Tool '{req.tool}' tidak tersedia. Pilihan: {list(SCRAPER_DISPATCHER.keys())}")
    
    result = run_single_scraper(
        tool_name=req.tool,
        keyword=req.keyword,
        count=req.count,
        save_to_db=req.save_to_db
    )
    return result

@router.post("/all")
def trigger_all_scrapes(req: AllScrapeRequest):
    result = run_all_scrapers(
        keyword=req.keyword,
        count_per_tool=req.count_per_tool,
        save_to_db=req.save_to_db
    )
    return result

@router.get("/timeline")
def get_timeline(keyword: str = Query("karhutla", description="Kata kunci untuk timeline GDELT"), timespan: str = "30d"):
    return get_gdelt_timeline_data(keyword=keyword, timespan=timespan)
