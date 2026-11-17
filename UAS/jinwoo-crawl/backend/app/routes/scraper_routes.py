import threading
import time
import uuid
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.config import settings
from app.scrapers.unified_runner import run_single_scraper, run_all_scrapers, run_selected_scrapers, SCRAPER_DISPATCHER
from app.scrapers.gdelt_scraper import get_gdelt_timeline_data

router = APIRouter(prefix="/api/scrape", tags=["Scraping Controls"])

class SingleScrapeRequest(BaseModel):
    tool: str = Field(..., description="Nama tool (gdelt, tiktok_search, pyktok, facebook_pages, instaloader, tiktok_api, youtube_api)")
    keyword: str = Field("karhutla", description="Kata kunci isu/topik")
    count: int = Field(10, ge=1, le=50000, description="Jumlah target data")
    year_range: int = Field(5, ge=1, le=10, description="Rentang tahun terakhir (default: 5 tahun, atau 2 tahun)")
    save_to_db: bool = Field(True, description="Apakah hasil disimpan ke MongoDB")

class SelectedScrapeRequest(BaseModel):
    tools: List[str] = Field(default_factory=list, description="Daftar ID tools yang dipilih via checklist")
    keyword: str = Field("karhutla", description="Kata kunci isu/topik")
    count_per_tool: int = Field(15, ge=1, le=50000, description="Target data per tool terpilih")
    year_range: int = Field(5, ge=1, le=10, description="Rentang tahun terakhir (default: 5 tahun, atau 2 tahun)")
    save_to_db: bool = Field(True, description="Apakah hasil disimpan ke MongoDB")

class AllScrapeRequest(BaseModel):
    keyword: str = Field("karhutla", description="Kata kunci isu/topik untuk seluruh 7 tools")
    count_per_tool: int = Field(15, ge=1, le=50000, description="Jumlah data per tool")
    year_range: int = Field(5, ge=1, le=10, description="Rentang tahun terakhir (default: 5 tahun, atau 2 tahun)")
    save_to_db: bool = Field(True, description="Apakah hasil disimpan ke MongoDB")

@router.get("/tools")
def list_available_tools() -> Dict[str, Any]:
    """Menampilkan status konfigurasi dan ketersediaan seluruh 7 Tool & API Scraping aktif"""
    return {
        "total_tools": 7,
        "tools": [
            {
                "id": "gdelt",
                "name": "GDELT 2.0 & Berita ID",
                "platform": "Global & Indonesian News Media",
                "type": "Free Official API + Master Feed",
                "auth_required": False,
                "auth_status": "Ready (No key needed)",
                "description": "Mengambil berita global & nasional dari GDELT 2.0 Master Feed, GDELT DOC API, serta portal berita Indonesia."
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
                "description": "Mengambil video berita dan komentar publik riil beserta metrik views, likes, dan diskusi."
            }
        ]
    }

_SCRAPE_JOBS: Dict[str, Dict[str, Any]] = {}
_JOBS_LOCK = threading.Lock()


@router.post("/start")
def start_single_scrape_job(req: SingleScrapeRequest):
    """Mulai crawling di background agar request HTTP bebas dari timeout Cloudflare 100 detik."""
    if req.tool not in SCRAPER_DISPATCHER:
        raise HTTPException(status_code=400, detail=f"Tool '{req.tool}' tidak tersedia. Pilihan: {list(SCRAPER_DISPATCHER.keys())}")

    job_id = uuid.uuid4().hex
    now = time.time()
    with _JOBS_LOCK:
        stale_keys = [
            k for k, v in _SCRAPE_JOBS.items()
            if v.get("status") == "done" and (now - v.get("finished_at", now)) > 3600
        ]
        for k in stale_keys:
            _SCRAPE_JOBS.pop(k, None)
        _SCRAPE_JOBS[job_id] = {"job_id": job_id, "status": "running", "tool": req.tool, "started_at": now}

    def _worker():
        try:
            res = run_single_scraper(
                tool_name=req.tool,
                keyword=req.keyword,
                count=req.count,
                year_range=req.year_range,
                save_to_db=req.save_to_db,
            )
        except Exception as e:
            res = {"tool": req.tool, "status": "error", "count": 0, "message": str(e), "items": []}
        with _JOBS_LOCK:
            _SCRAPE_JOBS[job_id] = {
                "job_id": job_id,
                "status": "done",
                "tool": req.tool,
                "finished_at": time.time(),
                "result": res,
            }

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return {"job_id": job_id, "status": "running", "tool": req.tool}


@router.get("/job/{job_id}")
def get_scrape_job_status(job_id: str):
    """Cek status eksekusi job background dari UI."""
    with _JOBS_LOCK:
        job = _SCRAPE_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job crawling tidak ditemukan atau sudah kedaluwarsa.")
    return job


@router.post("/single")
def trigger_single_scrape(req: SingleScrapeRequest):
    if req.tool not in SCRAPER_DISPATCHER:
        raise HTTPException(status_code=400, detail=f"Tool '{req.tool}' tidak tersedia. Pilihan: {list(SCRAPER_DISPATCHER.keys())}")
    
    result = run_single_scraper(
        tool_name=req.tool,
        keyword=req.keyword,
        count=req.count,
        year_range=req.year_range,
        save_to_db=req.save_to_db
    )
    return result

@router.post("/selected")
def trigger_selected_scrapes(req: SelectedScrapeRequest):
    result = run_selected_scrapers(
        tool_names=req.tools,
        keyword=req.keyword,
        count_per_tool=req.count_per_tool,
        year_range=req.year_range,
        save_to_db=req.save_to_db
    )
    return result

@router.post("/all")
def trigger_all_scrapes(req: AllScrapeRequest):
    result = run_all_scrapers(
        keyword=req.keyword,
        count_per_tool=req.count_per_tool,
        year_range=req.year_range,
        save_to_db=req.save_to_db
    )
    return result

@router.get("/timeline")
def get_timeline(keyword: str = Query("karhutla", description="Kata kunci untuk timeline GDELT"), timespan: str = "30d"):
    return get_gdelt_timeline_data(keyword=keyword, timespan=timespan)
