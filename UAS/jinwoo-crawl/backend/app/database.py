from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId
from app.config import settings

_client: Optional[MongoClient] = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client

def get_collection() -> Collection:
    client = get_client()
    db = client[settings.MONGODB_DB_NAME]
    return db[settings.MONGODB_COLLECTION]

def check_db_health() -> Dict[str, Any]:
    try:
        client = get_client()
        client.admin.command("ping")
        col = get_collection()
        count = col.count_documents({})
        return {
            "status": "connected",
            "database": settings.MONGODB_DB_NAME,
            "collection": settings.MONGODB_COLLECTION,
            "total_documents": count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "database": settings.MONGODB_DB_NAME,
            "collection": settings.MONGODB_COLLECTION,
            "total_documents": 0
        }

def save_scraped_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not items:
        return {"inserted_count": 0, "status": "no_items"}

    col = get_collection()
    now_iso = datetime.now(timezone.utc).isoformat()
    prepared_items = []
    
    for item in items:
        clean_item = dict(item)
        if "collected_at" not in clean_item:
            clean_item["collected_at"] = now_iso
        # Ensure unique id or fallback
        if "id" not in clean_item or not clean_item["id"]:
            clean_item["id"] = f"{clean_item.get('tool_source', 'src')}_{int(datetime.now().timestamp() * 1000)}"
        prepared_items.append(clean_item)

    # Use ordered=False to avoid aborting on duplicates
    result = col.insert_many(prepared_items, ordered=False)
    return {
        "inserted_count": len(result.inserted_ids),
        "status": "success"
    }

def get_scraped_items(
    limit: int = 100,
    skip: int = 0,
    tool_source: Optional[str] = None,
    keyword: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    col = get_collection()
    query: Dict[str, Any] = {}
    
    if tool_source and tool_source != "all":
        query["tool_source"] = tool_source
    if keyword:
        query["keyword"] = {"$regex": keyword, "$options": "i"}
    if category and category != "all":
        query["category"] = category

    cursor = col.find(query).sort("collected_at", pymongo.DESCENDING).skip(skip).limit(limit)
    documents = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        documents.append(doc)
    return documents

def get_dashboard_stats() -> Dict[str, Any]:
    col = get_collection()
    total_docs = col.count_documents({})
    
    # Aggregation per tool_source
    pipeline_tools = [
        {"$group": {"_id": "$tool_source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_tool = list(col.aggregate(pipeline_tools))
    tool_distribution = {item["_id"] or "unknown": item["count"] for item in by_tool}

    # Aggregation per platform
    pipeline_platform = [
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_platform = list(col.aggregate(pipeline_platform))
    platform_distribution = {item["_id"] or "unknown": item["count"] for item in by_platform}

    # Aggregation per category
    pipeline_cat = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_cat = list(col.aggregate(pipeline_cat))
    category_distribution = {item["_id"] or "General": item["count"] for item in by_cat}

    # Timeline aggregation (published_date or collected_at)
    pipeline_timeline = [
        {
            "$project": {
                "date": {
                    "$cond": [
                        {"$and": [{"$ne": ["$published_date", None]}, {"$ne": ["$published_date", ""]}]},
                        "$published_date",
                        {"$substr": ["$collected_at", 0, 10]}
                    ]
                },
                "tone": {"$ifNull": ["$metrics.sentiment_tone", 0]}
            }
        },
        {
            "$group": {
                "_id": "$date",
                "count": {"$sum": 1},
                "avg_tone": {"$avg": "$tone"}
            }
        },
        {"$sort": {"_id": 1}},
        {"$limit": 30}
    ]
    timeline_raw = list(col.aggregate(pipeline_timeline))
    timeline_data = [
        {
            "date": item["_id"],
            "count": item["count"],
            "avg_tone": round(float(item.get("avg_tone", 0.0)), 2)
        }
        for item in timeline_raw if item["_id"]
    ]

    return {
        "total_documents": total_docs,
        "tools": tool_distribution,
        "platforms": platform_distribution,
        "categories": category_distribution,
        "timeline": timeline_data
    }

def clear_all_items() -> int:
    col = get_collection()
    res = col.delete_many({})
    return res.deleted_count
