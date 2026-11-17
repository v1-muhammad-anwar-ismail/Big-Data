"""Real YouTube Data API v3 scraper: videos (search.list) + real public netizen comments (commentThreads.list)."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import re
import time
from typing import Any, Dict, List, Optional
import requests
from app.config import settings
from app.scrapers._helpers import (
    categorize_topic,
    estimate_tone,
    is_spam_or_judol,
    is_within_years,
    make_doc_id,
)


def _fetch_video_comments(
    api_key: str,
    video_meta: Dict[str, Any],
    keyword: str,
    year_range: int,
    max_comments_for_vid: int,
) -> List[Dict[str, Any]]:
    """Fetch paginated top-level comments for one YouTube video via REST API (thread-safe, 1 unit/100 comments)."""
    vid_id = video_meta["vid_id"]
    vid_title = video_meta["title"]
    channel = video_meta["channel"]
    thumb_url = video_meta["thumb_url"]

    collected: List[Dict[str, Any]] = []
    page_token: Optional[str] = None
    max_pages = max(1, (max_comments_for_vid + 99) // 100)

    for _ in range(max_pages):
        params: Dict[str, Any] = {
            "key": api_key,
            "part": "snippet",
            "videoId": vid_id,
            "maxResults": 100,
            "order": "relevance",
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token
        try:
            r = requests.get("https://www.googleapis.com/youtube/v3/commentThreads", params=params, timeout=(4, 8))
            if r.status_code != 200:
                break
            data = r.json()
        except Exception:
            break

        for thread in data.get("items", []):
            top = (thread.get("snippet") or {}).get("topLevelComment") or {}
            cid = top.get("id") or thread.get("id") or ""
            sn = top.get("snippet") or {}
            text = re.sub(r"\s+", " ", (sn.get("textDisplay") or "").strip())
            if not cid or len(text) < 12:
                continue
            if is_spam_or_judol(text, vid_title, ""):
                continue

            pub_at = sn.get("publishedAt") or video_meta["published_at"]
            try:
                dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)
            if not is_within_years(dt, year_range):
                continue

            author = (sn.get("authorDisplayName") or "YouTube User").strip()
            likes = int(sn.get("likeCount") or 0)
            replies = int((thread.get("snippet") or {}).get("totalReplyCount") or 0)
            comment_url = f"https://www.youtube.com/watch?v={vid_id}&lc={cid}"
            headline = text[:85] + ("..." if len(text) > 85 else "")
            cat = categorize_topic(f"{vid_title} {text}")

            collected.append({
                "id": make_doc_id("yt_cmt", cid),
                "tool_source": "youtube_api",
                "platform": "YouTube",
                "keyword": keyword,
                "category": cat,
                "title": f"Komentar {author}: {headline}",
                "content": f"{text}\n\n[Pada Video: {vid_title} — {channel}]"[:1500],
                "url": comment_url,
                "thumbnail_url": thumb_url,
                "author_or_source": f"YouTube Komentar: {author}",
                "published_at": pub_at,
                "published_date": pub_at[:10],
                "metrics": {
                    "views": 0,
                    "likes": likes,
                    "comments": replies,
                    "shares": 0,
                    "sentiment_tone": estimate_tone(text),
                },
                "raw_data": {"comment_id": cid, "video_id": vid_id, "type": "comment"},
            })
            if len(collected) >= max_comments_for_vid:
                break

        page_token = data.get("nextPageToken")
        if not page_token or len(collected) >= max_comments_for_vid:
            break

    return collected


def scrape_youtube_api(keyword: str = "karhutla", max_results: int = 15, year_range: int = 5) -> List[Dict[str, Any]]:
    api_key = settings.YOUTUBE_API_KEY.strip()
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY belum diisi di .env")

    from googleapiclient.discovery import build

    youtube = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
    cutoff_year = max(2015, datetime.now(timezone.utc).year - max(1, int(year_range)))
    published_after = f"{cutoff_year}-01-01T00:00:00Z"

    results: List[Dict[str, Any]] = []
    video_metas: List[Dict[str, Any]] = []
    seen_ids: set = set()
    page_token: Optional[str] = None
    target = max(1, min(int(max_results), 50000))
    video_cap = min(target, 500)

    while len(results) < video_cap:
        batch_size = min(50, video_cap - len(results))
        search_kwargs: Dict[str, Any] = {
            "q": keyword,
            "part": "snippet",
            "type": "video",
            "order": "relevance",
            "publishedAfter": published_after,
            "regionCode": "ID",
            "maxResults": batch_size,
        }
        if page_token:
            search_kwargs["pageToken"] = page_token

        try:
            search_response = youtube.search().list(**search_kwargs).execute()
        except Exception as e:
            if results:
                print(f"[YouTube API] Pagination video berhenti di {len(results)}: {e}", flush=True)
                break
            raise
        items = search_response.get("items", [])
        if not items:
            break

        video_ids = [
            it["id"]["videoId"]
            for it in items
            if it.get("id", {}).get("videoId") and it["id"]["videoId"] not in seen_ids
        ]
        if not video_ids:
            break

        details_map: Dict[str, Dict[str, Any]] = {}
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i : i + 50]
            vid_resp = youtube.videos().list(part="statistics,snippet", id=",".join(chunk)).execute()
            for v_it in vid_resp.get("items", []):
                details_map[v_it["id"]] = v_it

        for it in items:
            v_id = it.get("id", {}).get("videoId", "")
            if not v_id or v_id in seen_ids:
                continue
            seen_ids.add(v_id)

            detail = details_map.get(v_id, {})
            snippet = detail.get("snippet") or it.get("snippet") or {}
            stats = detail.get("statistics") or {}

            title = (snippet.get("title") or "").strip()
            desc = (snippet.get("description") or "").strip() or title
            if is_spam_or_judol(desc, title, f"https://www.youtube.com/watch?v={v_id}"):
                continue
            channel = snippet.get("channelTitle") or "YouTube Channel"
            published_at = snippet.get("publishedAt") or datetime.now(timezone.utc).isoformat()
            p_date = published_at[:10]

            thumbs = snippet.get("thumbnails") or {}
            thumb_url = (
                (thumbs.get("maxres") or {}).get("url")
                or (thumbs.get("high") or {}).get("url")
                or (thumbs.get("medium") or {}).get("url")
                or f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"
            )

            views = int(stats.get("viewCount") or 0)
            likes = int(stats.get("likeCount") or 0)
            comments_cnt = int(stats.get("commentCount") or 0)
            cat = categorize_topic(f"{title} {desc}")

            results.append({
                "id": make_doc_id("yt", v_id),
                "tool_source": "youtube_api",
                "platform": "YouTube",
                "keyword": keyword,
                "category": cat,
                "title": title,
                "content": desc[:1500],
                "url": f"https://www.youtube.com/watch?v={v_id}",
                "thumbnail_url": thumb_url,
                "author_or_source": f"YouTube: {channel}",
                "published_at": published_at,
                "published_date": p_date,
                "metrics": {
                    "views": views,
                    "likes": likes,
                    "comments": comments_cnt,
                    "shares": 0,
                    "sentiment_tone": estimate_tone(f"{title} {desc}"),
                },
                "raw_data": {"video_id": v_id, "channel_id": snippet.get("channelId"), "stats": stats, "type": "video"},
            })
            video_metas.append({
                "vid_id": v_id,
                "title": title,
                "channel": channel,
                "thumb_url": thumb_url,
                "published_at": published_at,
                "comment_count": comments_cnt,
            })
            if len(results) >= video_cap:
                break

        page_token = search_response.get("nextPageToken")
        if not page_token:
            break

    print(f"[YouTube API] Video terkumpul: {len(results)} (target total={target})", flush=True)

    # Expand to real public YouTube comments when requested target exceeds discovered videos
    if len(results) < target and video_metas:
        needed = target - len(results)
        comment_videos = sorted(
            [v for v in video_metas if v["comment_count"] > 0],
            key=lambda x: x["comment_count"],
            reverse=True,
        )
        if comment_videos:
            # Allocate pages fairly while respecting per-video comment availability and big targets (up to ~1000/video)
            per_vid_cap = min(1000, max(100, (needed // max(1, min(len(comment_videos), 80))) + 100))
            seen_comment_keys: set = set()
            t_cmt = time.time()
            print(f"[YouTube API] Mengambil komentar netizen dari {len(comment_videos)} video...", flush=True)

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [
                    executor.submit(_fetch_video_comments, api_key, vm, keyword, year_range, per_vid_cap)
                    for vm in comment_videos
                ]
                done_vids = 0
                for fut in as_completed(futures):
                    done_vids += 1
                    try:
                        cmt_list = fut.result()
                        for c_item in cmt_list:
                            if len(results) >= target:
                                break
                            dedup_key = f"{c_item['author_or_source'].lower()}|{c_item['title'].lower()}"
                            if dedup_key in seen_comment_keys:
                                continue
                            seen_comment_keys.add(dedup_key)
                            results.append(c_item)
                    except Exception:
                        pass
                    if done_vids % 25 == 0 or len(results) >= target:
                        print(
                            f"[YouTube API] Progres total (video + komentar): {len(results):,}/{target:,} ({time.time() - t_cmt:.1f}s)",
                            flush=True,
                        )
                    if len(results) >= target:
                        for rem in futures:
                            rem.cancel()
                        break

    return results[:target]
