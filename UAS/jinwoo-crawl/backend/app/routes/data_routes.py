import csv
import io
import json
from fastapi import APIRouter, Query, Response
from typing import Optional, List, Dict, Any
from app.database import get_scraped_items, get_dashboard_stats, clear_all_items

router = APIRouter(prefix="/api/data", tags=["Dataset & Analytics"])

@router.get("/items")
def list_items(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    tool_source: Optional[str] = Query(None, description="Filter sumber tool"),
    keyword: Optional[str] = Query(None, description="Filter kata kunci"),
    category: Optional[str] = Query(None, description="Filter kategori berita (Disaster, Politics, Economy, etc.)")
):
    items = get_scraped_items(limit=limit, skip=skip, tool_source=tool_source, keyword=keyword, category=category)
    return {
        "count": len(items),
        "limit": limit,
        "skip": skip,
        "items": items
    }

@router.get("/stats")
def dashboard_stats():
    return get_dashboard_stats()

@router.delete("/clear")
def clear_dataset():
    deleted_count = clear_all_items()
    return {
        "status": "success",
        "deleted_count": deleted_count,
        "message": f"Berhasil mengosongkan {deleted_count} dokumen dari MongoDB."
    }

@router.get("/export/json")
def export_dataset_json():
    """Ekspor seluruh dataset MongoDB ke format JSON siap unggah ke HDFS"""
    items = get_scraped_items(limit=50000)
    json_bytes = json.dumps(items, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=jinwoo_crawl_dataset.json"}
    )

@router.get("/export/csv")
def export_dataset_csv():
    """Ekspor dataset MongoDB ke format CSV siap dibaca oleh Apache Spark DataFrame"""
    items = get_scraped_items(limit=50000)
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "id", "tool_source", "platform", "keyword", "category",
        "title", "author_or_source", "published_date",
        "views", "likes", "comments", "shares", "sentiment_tone", "url"
    ])
    
    for item in items:
        m = item.get("metrics", {})
        writer.writerow([
            item.get("id", ""),
            item.get("tool_source", ""),
            item.get("platform", ""),
            item.get("keyword", ""),
            item.get("category", ""),
            item.get("title", "").replace("\n", " "),
            item.get("author_or_source", ""),
            item.get("published_date", ""),
            m.get("views", 0),
            m.get("likes", 0),
            m.get("comments", 0),
            m.get("shares", 0),
            m.get("sentiment_tone", 0.0),
            item.get("url", "")
        ])
        
    csv_bytes = output.getvalue().encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jinwoo_crawl_dataset.csv"}
    )
