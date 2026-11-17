from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId
from app.config import settings
from app.scrapers._helpers import canonicalize_url, compute_content_hash, is_spam_or_judol

_client: Optional[MongoClient] = None
_indexes_ready: bool = False

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client

def get_collection() -> Collection:
    global _indexes_ready
    client = get_client()
    db = client[settings.MONGODB_DB_NAME]
    col = db[settings.MONGODB_COLLECTION]
    if not _indexes_ready:
        try:
            col.create_index("id")
            col.create_index("canonical_url")
            col.create_index("content_hash")
            col.create_index([("collected_at", pymongo.DESCENDING)])
            col.create_index("tool_source")
            _indexes_ready = True
        except Exception:
            pass
    return col

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

def get_existing_identity_maps() -> tuple[Dict[str, str], Dict[str, str]]:
    """Return existing canonical_url -> doc_id and content_hash -> doc_id maps for cross-tool dedup."""
    col = get_collection()
    existing_url_to_id: Dict[str, str] = {}
    existing_hash_to_id: Dict[str, str] = {}
    for doc in col.find({}, {"id": 1, "url": 1, "canonical_url": 1, "content_hash": 1, "title": 1, "content": 1, "author_or_source": 1}):
        doc_id = str(doc.get("id") or doc.get("_id") or "")
        cu = doc.get("canonical_url") or canonicalize_url(doc.get("url", ""))
        ch = doc.get("content_hash") or compute_content_hash(doc)
        if cu and cu not in existing_url_to_id:
            existing_url_to_id[cu] = doc_id
        if ch and ch not in existing_hash_to_id:
            existing_hash_to_id[ch] = doc_id
    return existing_url_to_id, existing_hash_to_id


def save_scraped_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not items:
        return {"inserted_count": 0, "status": "no_items"}

    col = get_collection()
    now_iso = datetime.now(timezone.utc).isoformat()
    ops = []

    existing_ids: set = set()
    existing_url_to_id: Dict[str, str] = {}
    existing_hash_to_id: Dict[str, str] = {}
    for doc in col.find({}, {"id": 1, "url": 1, "canonical_url": 1, "content_hash": 1, "title": 1, "content": 1, "author_or_source": 1}):
        doc_id = str(doc.get("id") or doc.get("_id") or "")
        if doc_id:
            existing_ids.add(doc_id)
        cu = doc.get("canonical_url") or canonicalize_url(doc.get("url", ""))
        ch = doc.get("content_hash") or compute_content_hash(doc)
        if cu and cu not in existing_url_to_id:
            existing_url_to_id[cu] = doc_id
        if ch and ch not in existing_hash_to_id:
            existing_hash_to_id[ch] = doc_id

    skipped_duplicates = 0
    skipped_spam = 0

    for item in items:
        if (item.get("tool_source") or "").lower() == "meta_ad_library":
            skipped_spam += 1
            continue
        if is_spam_or_judol(item.get("content", ""), item.get("title", ""), item.get("url", "")):
            skipped_spam += 1
            continue

        clean_item = dict(item)
        if "collected_at" not in clean_item:
            clean_item["collected_at"] = now_iso
        if "id" not in clean_item or not clean_item["id"]:
            clean_item["id"] = f"{clean_item.get('tool_source', 'src')}_{int(datetime.now().timestamp() * 1000)}"

        doc_id = str(clean_item["id"])
        canon_url = canonicalize_url(clean_item.get("url", ""))
        c_hash = compute_content_hash(clean_item)

        if canon_url and canon_url in existing_url_to_id and existing_url_to_id[canon_url] != doc_id:
            skipped_duplicates += 1
            continue
        if c_hash and c_hash in existing_hash_to_id and existing_hash_to_id[c_hash] != doc_id:
            skipped_duplicates += 1
            continue

        clean_item["canonical_url"] = canon_url
        clean_item["content_hash"] = c_hash
        if canon_url:
            existing_url_to_id[canon_url] = doc_id
        if c_hash:
            existing_hash_to_id[c_hash] = doc_id

        if doc_id in existing_ids:
            ops.append(pymongo.UpdateOne({"id": doc_id}, {"$set": clean_item}, upsert=True))
        else:
            existing_ids.add(doc_id)
            ops.append(pymongo.InsertOne(clean_item))

    if not ops:
        return {
            "inserted_count": 0,
            "upserted_count": 0,
            "updated_count": 0,
            "total_processed": 0,
            "skipped_duplicates": skipped_duplicates,
            "skipped_spam": skipped_spam,
            "status": "dedup_filtered",
        }

    result = col.bulk_write(ops, ordered=False)
    inserted_total = result.inserted_count + result.upserted_count
    saved = inserted_total + result.modified_count + result.matched_count
    return {
        "inserted_count": inserted_total or len(ops),
        "upserted_count": inserted_total,
        "updated_count": result.modified_count,
        "total_processed": saved,
        "skipped_duplicates": skipped_duplicates,
        "skipped_spam": skipped_spam,
        "status": "success",
    }

_TOOL_FILTER_MAP: Dict[str, Dict[str, Any]] = {
    "gdelt": {"tool_source": "gdelt"},
    "news": {"tool_source": "gdelt"},
    "tiktok_search": {"tool_source": "tiktok_search"},
    "tiktok_api": {"tool_source": "tiktok_api"},
    "pyktok": {"tool_source": "pyktok"},
    "tiktok": {"$or": [{"tool_source": {"$in": ["tiktok_search", "tiktok_api", "pyktok"]}}, {"platform": "TikTok"}]},
    "youtube": {"tool_source": "youtube_api"},
    "youtube_api": {"tool_source": "youtube_api"},
    "instagram": {"tool_source": "instaloader"},
    "instaloader": {"tool_source": "instaloader"},
    "facebook": {"tool_source": "facebook_pages"},
    "facebook_pages": {"tool_source": "facebook_pages"},
}

def get_scraped_items(
    limit: int = 50000,
    skip: int = 0,
    tool_source: Optional[str] = None,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[str] = None,
    include_raw: bool = False
) -> List[Dict[str, Any]]:
    col = get_collection()
    query: Dict[str, Any] = {}
    
    if tool_source and tool_source != "all":
        tool_clean = tool_source.strip().lower()
        if tool_clean in _TOOL_FILTER_MAP:
            query.update(_TOOL_FILTER_MAP[tool_clean])
        else:
            query["tool_source"] = tool_source
    else:
        query["tool_source"] = {"$ne": "meta_ad_library"}
    if keyword:
        query["keyword"] = {"$regex": keyword, "$options": "i"}
    if category and category != "all":
        query["category"] = category
    if year and year != "all":
        query["published_date"] = {"$regex": f"^{year}"}

    projection = None if include_raw else {"raw_data": 0}
    cursor = col.find(query, projection).sort("collected_at", pymongo.DESCENDING).skip(skip).limit(limit)
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


def purge_unwanted_and_duplicates() -> Dict[str, int]:
    """Remove retired meta_ad_library docs, judol/spam items, and URL/content duplicates."""
    col = get_collection()
    res_meta = col.delete_many({"tool_source": "meta_ad_library"})
    removed_meta = res_meta.deleted_count

    seen_urls: set = set()
    seen_hashes: set = set()
    dup_ids: List[Any] = []
    spam_ids: List[Any] = []

    for doc in col.find({}, {"_id": 1, "url": 1, "title": 1, "content": 1, "author_or_source": 1}):
        if is_spam_or_judol(doc.get("content", ""), doc.get("title", ""), doc.get("url", "")):
            spam_ids.append(doc["_id"])
            continue
        cu = canonicalize_url(doc.get("url", ""))
        ch = compute_content_hash(doc)
        if (cu and cu in seen_urls) or (ch and ch in seen_hashes):
            dup_ids.append(doc["_id"])
            continue
        if cu:
            seen_urls.add(cu)
        if ch:
            seen_hashes.add(ch)

    removed_spam = col.delete_many({"_id": {"$in": spam_ids}}).deleted_count if spam_ids else 0
    removed_dups = col.delete_many({"_id": {"$in": dup_ids}}).deleted_count if dup_ids else 0
    return {
        "removed_meta_ads": removed_meta,
        "removed_spam_judol": removed_spam,
        "removed_duplicates": removed_dups,
        "remaining_total": col.count_documents({}),
    }
