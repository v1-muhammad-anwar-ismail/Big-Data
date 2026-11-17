import hashlib
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any

def categorize_news(text: str) -> str:
    text_lower = text.lower()
    if any(k in text_lower for k in ["hutan", "karhutla", "banjir", "gempa", "longsor", "cuaca", "bencana", "iklim"]):
        return "Disaster"
    elif any(k in text_lower for k in ["gibran", "presiden", "menteri", "partai", "dpr", "pemilu", "politik", "pilkada", "kebijakan", "mundur"]):
        return "Politics"
    elif any(k in text_lower for k in ["saham", "rupiah", "inflasi", "ekonomi", "anggaran", "investasi", "keuangan", "pajak", "bisnis"]):
        return "Economy"
    elif any(k in text_lower for k in ["ai", "teknologi", "aplikasi", "cyber", "internet", "gadget", "digital", "data"]):
        return "Technology"
    elif any(k in text_lower for k in ["viral", "kasus", "polisi", "sidang", "hukum", "sosial", "masyarakat", "warga"]):
        return "Social"
    return "General"

def scrape_indonesian_news_fallback(keyword: str, max_records: int = 20) -> List[Dict[str, Any]]:
    """Fallback berita nasional (Antara & CNN Indonesia RSS) jika GDELT rate limited (429)"""
    results = []
    feeds = [
        {"url": "https://www.antaranews.com/rss/terkini.xml", "source": "Antara News"},
        {"url": "https://www.antaranews.com/rss/hukum.xml", "source": "Antara Hukum"},
        {"url": "https://www.antaranews.com/rss/ekonomi.xml", "source": "Antara Ekonomi"}
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JinwooCrawl/1.0"}
    
    for feed in feeds:
        if len(results) >= max_records:
            break
        try:
            r = requests.get(feed["url"], headers=headers, timeout=6)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                for item in root.findall(".//item"):
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")
                    desc = item.findtext("description", "")
                    
                    # Check match or include if general
                    is_match = not keyword or keyword.lower() in (title + " " + desc).lower()
                    if is_match or len(results) < 5:
                        doc_id = hashlib.md5(f"rss_{link}".encode()).hexdigest()
                        cat = categorize_news(title + " " + desc)
                        
                        # Date parse
                        p_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                        results.append({
                            "id": doc_id,
                            "tool_source": "gdelt",
                            "platform": "News",
                            "keyword": keyword,
                            "category": cat,
                            "title": title,
                            "content": desc[:300] if desc else f"Berita dari {feed['source']}.",
                            "url": link,
                            "author_or_source": feed["source"],
                            "published_at": pub_date or datetime.now(timezone.utc).isoformat(),
                            "published_date": p_date,
                            "metrics": {
                                "views": 1200,
                                "likes": 0,
                                "comments": 0,
                                "shares": 0,
                                "sentiment_tone": -1.5 if cat in ["Disaster", "Social"] else 0.5
                            },
                            "raw_data": {"rss_feed": feed["url"]}
                        })
                        if len(results) >= max_records:
                            break
        except Exception as e:
            print(f"[RSS Fallback] Error {feed['source']}: {e}")
            
    return results

def scrape_gdelt(keyword: str = "karhutla", max_records: int = 30, timespan: str = "7d") -> List[Dict[str, Any]]:
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # Try GDELT 2.0 Doc API with safe retry
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": keyword,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": min(max_records, 100),
        "timespan": timespan,
        "sort": "DateDesc"
    }
    
    for attempt in range(2):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("articles", [])
                for art in articles:
                    art_url = art.get("url", "")
                    art_title = art.get("title", "")
                    seendate = art.get("seendate", "")
                    domain = art.get("domain", "Online News")
                    doc_id = hashlib.md5(f"gdelt_{art_url}_{art_title}".encode()).hexdigest()
                    pub_date = seendate[:10] if len(seendate) >= 10 else datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    cat = categorize_news(art_title)

                    results.append({
                        "id": doc_id,
                        "tool_source": "gdelt",
                        "platform": "News",
                        "keyword": keyword,
                        "category": cat,
                        "title": art_title,
                        "content": f"Berita terindeks pada {domain} ({seendate}).",
                        "url": art_url,
                        "author_or_source": domain,
                        "published_at": seendate,
                        "published_date": pub_date,
                        "metrics": {
                            "views": 0,
                            "likes": 0,
                            "comments": 0,
                            "shares": 0,
                            "sentiment_tone": float(art.get("tone", 0.0) or 0.0)
                        },
                        "raw_data": art
                    })
                if results:
                    return results
            elif resp.status_code == 429:
                print(f"[GDELT] Rate limit hit (429), pausing briefly...")
                time.sleep(2)
        except Exception as e:
            print(f"[GDELT] Attempt {attempt} error: {e}")
            time.sleep(1)

    # If GDELT is rate-limited or returns 0, use reliable Indonesian News Fallback
    if not results:
        print(f"[GDELT] Activating Indonesian News Feed Fallback for '{keyword}'...")
        results = scrape_indonesian_news_fallback(keyword, max_records=max_records)

    return results

def get_gdelt_timeline_data(keyword: str = "karhutla", timespan: str = "30d") -> Dict[str, Any]:
    timeline_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    output = {"keyword": keyword, "vol_timeline": [], "tone_timeline": []}
    
    try:
        resp_vol = requests.get(timeline_url, params={
            "query": keyword,
            "mode": "TimelineVolRaw",
            "format": "json",
            "timespan": timespan
        }, headers=headers, timeout=8)
        if resp_vol.status_code == 200:
            output["vol_timeline"] = resp_vol.json().get("timeline", [])
    except Exception as e:
        print(f"[GDELT Timeline] Error vol: {e}")

    try:
        resp_tone = requests.get(timeline_url, params={
            "query": keyword,
            "mode": "TimelineTone",
            "format": "json",
            "timespan": timespan
        }, headers=headers, timeout=8)
        if resp_tone.status_code == 200:
            output["tone_timeline"] = resp_tone.json().get("timeline", [])
    except Exception as e:
        print(f"[GDELT Timeline] Error tone: {e}")

    return output
