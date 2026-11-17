"""Real news scraper: GDELT 2.0 Master Feed + DOC API + Detik + Kompas + Antara + Indonesian RSS."""
import io
import re
import threading
import time
import zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup
from app.scrapers._helpers import (
    UA,
    canonicalize_url,
    categorize_topic,
    estimate_tone,
    is_spam_or_judol,
    is_within_years,
    make_doc_id,
    matches_keyword,
)

_GDELT_LOCK = threading.Lock()
_LAST_GDELT_CALL = 0.0

_MONTHS_ID = {
    "jan": 1, "januari": 1, "feb": 2, "februari": 2, "mar": 3, "maret": 3,
    "apr": 4, "april": 4, "mei": 5, "jun": 6, "juni": 6, "jul": 7, "juli": 7,
    "agu": 8, "agustus": 8, "aug": 8, "sep": 9, "september": 9,
    "okt": 10, "oktober": 10, "oct": 10, "nov": 11, "november": 11, "des": 12, "desember": 12, "dec": 12,
}


def _parse_gdelt_seendate(seendate: str) -> datetime:
    m = re.match(r"(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})", seendate or "")
    if m:
        return datetime(*map(int, m.groups()), tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _parse_indonesian_date(raw: str) -> datetime:
    text = (raw or "").strip().lower()
    now = datetime.now(timezone.utc)
    rel = re.search(r"(\d+)\s*(detik|menit|jam|hari|minggu)", text)
    if rel and "lalu" in text:
        val, unit = int(rel.group(1)), rel.group(2)
        delta = {
            "detik": timedelta(seconds=val),
            "menit": timedelta(minutes=val),
            "jam": timedelta(hours=val),
            "hari": timedelta(days=val),
            "minggu": timedelta(weeks=val),
        }.get(unit, timedelta())
        return now - delta
    m = re.search(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})(?:\s+(\d{1,2}):(\d{2}))?", text)
    if m:
        day, mon_str, yr = int(m.group(1)), m.group(2), int(m.group(3))
        hh = int(m.group(4) or 0)
        mm = int(m.group(5) or 0)
        mon = _MONTHS_ID.get(mon_str[:3]) or _MONTHS_ID.get(mon_str)
        if mon:
            try:
                return datetime(yr, mon, day, hh, mm, tzinfo=timezone.utc)
            except ValueError:
                pass
    return now


def _build_news_item(
    id_prefix: str,
    keyword: str,
    title: str,
    content: str,
    url: str,
    thumb: str,
    source: str,
    dt: datetime,
    raw_data: Dict[str, Any],
    tone: float | None = None,
) -> Dict[str, Any]:
    return {
        "id": make_doc_id(id_prefix, canonicalize_url(url) or url),
        "tool_source": "gdelt",
        "platform": "News",
        "keyword": keyword,
        "category": categorize_topic(f"{title} {content}"),
        "title": title,
        "content": content or title,
        "url": url,
        "thumbnail_url": thumb,
        "author_or_source": source or "Online News",
        "published_at": dt.isoformat(),
        "published_date": dt.strftime("%Y-%m-%d"),
        "metrics": {
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "sentiment_tone": float(tone) if tone is not None else estimate_tone(f"{title} {content}"),
        },
        "raw_data": raw_data,
    }


def _scrape_gdelt_api(keyword: str, max_records: int, timespan: str, seen_urls: set) -> List[Dict[str, Any]]:
    global _LAST_GDELT_CALL
    results: List[Dict[str, Any]] = []
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": keyword,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": min(max_records, 250),
        "timespan": timespan,
        "sort": "DateDesc",
    }

    print(f"[GDELT API] Mencari '{keyword}' (timespan={timespan})...", flush=True)
    with _GDELT_LOCK:
        for attempt in range(2):
            elapsed = time.time() - _LAST_GDELT_CALL
            if _LAST_GDELT_CALL > 0 and elapsed < 5.3:
                time.sleep(5.3 - elapsed)
            _LAST_GDELT_CALL = time.time()
            try:
                resp = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=(4, 6))
                if resp.status_code == 200:
                    data = resp.json()
                    for art in data.get("articles", []):
                        art_url = (art.get("url") or "").strip()
                        art_title = (art.get("title") or "").strip()
                        cu = canonicalize_url(art_url)
                        if not art_url or not art_title or cu in seen_urls or is_spam_or_judol(art_title, art_title, art_url):
                            continue
                        seen_urls.add(cu)
                        dt = _parse_gdelt_seendate(art.get("seendate", ""))
                        domain = art.get("domain") or "Online News"
                        results.append(_build_news_item(
                            id_prefix="gdelt",
                            keyword=keyword,
                            title=art_title,
                            content=f"Artikel berita terindeks GDELT 2.0 dari {domain} ({dt.strftime('%Y-%m-%d')}).",
                            url=art_url,
                            thumb=art.get("socialimage") or "",
                            source=domain,
                            dt=dt,
                            raw_data=art,
                            tone=float(art.get("tone")) if art.get("tone") else None,
                        ))
                    print(f"[GDELT API] Selesai: {len(results)} artikel.", flush=True)
                    return results
                if resp.status_code == 429 and attempt == 0:
                    print("[GDELT API] Rate limited (429), coba ulang 1x...", flush=True)
                    time.sleep(5.5)
                    continue
                print(f"[GDELT API] HTTP {resp.status_code}, lanjut ke GDELT Master Feed & Portal Berita...", flush=True)
                break
            except Exception as e:
                print(f"[GDELT API] Tidak tersedia ({e}), lanjut ke GDELT Master Feed & Portal Berita...", flush=True)
                break
    return results


def _fetch_gkg_zip(zip_url: str, keyword: str, year_range: int) -> List[Dict[str, Any]]:
    """Unduh satu file GDELT 2.0 GKG ZIP lalu filter artikel yang cocok dengan kata kunci."""
    found: List[Dict[str, Any]] = []
    try:
        r = requests.get(zip_url, headers={"User-Agent": UA}, timeout=(5, 14))
        if r.status_code != 200 or len(r.content) < 100 or not r.content[:2] == b"PK":
            return []
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            raw_text = zf.read(zf.namelist()[0]).decode("utf-8", errors="ignore")
        for line in raw_text.splitlines():
            cols = line.split("\t")
            if len(cols) < 16:
                continue
            art_url = cols[4].strip()
            if not art_url.startswith("http"):
                continue
            extra_xml = cols[26] if len(cols) > 26 else ""
            m_title = re.search(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", extra_xml, re.S)
            title = m_title.group(1).strip() if m_title else ""
            persons = cols[11] if len(cols) > 11 else ""
            orgs = cols[13] if len(cols) > 13 else ""
            themes = cols[7] if len(cols) > 7 else ""
            searchable = f"{title} {persons} {orgs} {art_url}"
            if not matches_keyword(searchable, keyword):
                continue
            if is_spam_or_judol(searchable, title, art_url):
                continue
            dt = _parse_gdelt_seendate((cols[1][:8] + "T" + cols[1][8:14]) if len(cols[1]) >= 14 else "")
            if not is_within_years(dt, year_range):
                continue
            domain = cols[3].strip() or "GDELT News"
            if not title:
                slug = art_url.rstrip("/").split("/")[-1].replace("-", " ").strip()
                title = f"[{domain}] {slug[:90]}" if slug else f"Berita {domain}: {keyword}"
            tone_raw = (cols[15].split(",")[0] if cols[15] else "").strip()
            try:
                tone_val: float | None = round(float(tone_raw), 2) if tone_raw else None
            except ValueError:
                tone_val = None
            thumb = (cols[18] if len(cols) > 18 else "").strip()
            snippet = f"GDELT Master GKG ({domain}) — Tokoh: {persons[:120] or '-'} | Org: {orgs[:120] or '-'} | Tema: {themes[:120] or '-'}"
            found.append(_build_news_item(
                id_prefix="gdelt_gkg",
                keyword=keyword,
                title=title,
                content=snippet,
                url=art_url,
                thumb=thumb if thumb.startswith("http") else "",
                source=domain,
                dt=dt,
                raw_data={"source": "gdelt_v2_gkg", "gkg_record_id": cols[0], "themes": themes[:160]},
                tone=tone_val,
            ))
    except Exception:
        pass
    return found


def _scrape_gdelt_master_feeds(keyword: str, max_needed: int, year_range: int, seen_urls: set) -> List[Dict[str, Any]]:
    """Ambil berita nyata dari file GDELT 2.0 Master CSV/GKG Feed (lastupdate + recent 15-min slices)."""
    zip_urls: List[str] = []
    base_ts: datetime | None = None
    for idx_url in ("http://data.gdeltproject.org/gdeltv2/lastupdate.txt",):
        try:
            r = requests.get(idx_url, headers={"User-Agent": UA}, timeout=(4, 6))
            if r.status_code == 200:
                for line in r.text.splitlines():
                    parts = line.strip().split()
                    if parts and parts[-1].endswith(".gkg.csv.zip"):
                        u = parts[-1]
                        zip_urls.append(u)
                        m_ts = re.search(r"/(\d{14})\.", u)
                        if m_ts:
                            base_ts = datetime.strptime(m_ts.group(1), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except Exception:
            pass

    if base_ts and max_needed >= 500:
        for step in range(1, 3):
            prev_ts = (base_ts - timedelta(minutes=15 * step)).strftime("%Y%m%d%H%M%S")
            zip_urls.append(f"http://data.gdeltproject.org/gdeltv2/{prev_ts}.gkg.csv.zip")

    if not zip_urls:
        return []

    print(f"[GDELT Master] Memindai {len(zip_urls)} feed GKG 2.0 untuk '{keyword}'...", flush=True)
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        for batch in executor.map(lambda zu: _fetch_gkg_zip(zu, keyword, year_range), zip_urls):
            for it in batch:
                cu = canonicalize_url(it["url"])
                if cu in seen_urls:
                    continue
                seen_urls.add(cu)
                results.append(it)
                if len(results) >= max_needed:
                    break
            if len(results) >= max_needed:
                break
    print(f"[GDELT Master] Selesai: {len(results)} artikel GKG cocok.", flush=True)
    return results


def _fetch_detik_page(keyword: str, page_num: int, year_range: int, year_slice: int | None = None) -> Dict[str, Any]:
    """Ambil dan parse satu halaman pencarian Detik.com (seluruh kanal/daerah)."""
    page_items: List[Dict[str, Any]] = []
    params: Dict[str, str] = {"query": keyword, "sortby": "time", "page": str(page_num)}
    if year_slice is not None:
        params["fromdatex"] = f"01/01/{year_slice}"
        params["todatex"] = f"31/12/{year_slice}"
    try:
        r = requests.get(
            "https://www.detik.com/search/searchall",
            params=params,
            headers={"User-Agent": UA},
            timeout=(5, 8),
        )
        if r.status_code != 200:
            return {"page": page_num, "items": [], "empty": True, "cutoff": False}
        soup = BeautifulSoup(r.text, "html.parser")
        articles = soup.select("article")
        if not articles:
            return {"page": page_num, "items": [], "empty": True, "cutoff": False}

        hit_cutoff = False
        for art in articles:
            a = art.select_one("a[href]")
            if not a:
                continue
            art_url = (a.get("href") or "").strip()
            if not art_url.startswith("http"):
                continue
            h = art.select_one(".media__title a, .media__title")
            title = (
                h.get_text(" ", strip=True)
                if h
                else (a.get("dtr-ttl") or a.get_text(" ", strip=True))
            )
            sub_el = art.select_one(".media__subtitle")
            channel = sub_el.get_text(" ", strip=True) if sub_el else "detik.com"
            if not title:
                continue
            dt_el = art.select_one(".media__date span[title], .media__date")
            raw_date = (dt_el.get("title") or dt_el.get("data-date") or dt_el.get_text(" ", strip=True)) if dt_el else ""
            dt = _parse_indonesian_date(raw_date)
            if not is_within_years(dt, year_range):
                hit_cutoff = True
                break
            img = art.select_one("img")
            thumb = (img.get("src") or img.get("data-src") or "") if img else ""
            desc_el = art.select_one(".media__desc")
            desc = desc_el.get_text(" ", strip=True) if desc_el else ""
            if is_spam_or_judol(desc, title, art_url):
                continue
            page_items.append(_build_news_item(
                id_prefix="gdelt_detik",
                keyword=keyword,
                title=title,
                content=desc or f"{title} — Liputan Detik.com ({dt.strftime('%Y-%m-%d')}).",
                url=art_url,
                thumb=thumb,
                source=channel or "detik.com",
                dt=dt,
                raw_data={"source": "detik_search", "raw_date": raw_date},
            ))
        return {"page": page_num, "items": page_items, "empty": False, "cutoff": hit_cutoff}
    except Exception as e:
        print(f"[Detik Search] Page {page_num} error: {e}", flush=True)
        return {"page": page_num, "items": [], "empty": False, "cutoff": False}


def _scrape_detik_search(keyword: str, max_needed: int, year_range: int, seen_urls: set) -> List[Dict[str, Any]]:
    """Detik.com real full-text search across archives (yearly windows for high targets)."""
    results: List[Dict[str, Any]] = []
    now_year = datetime.now(timezone.utc).year
    cutoff_year = max(2015, now_year - max(1, int(year_range)))
    year_slices: List[int | None] = (
        list(range(now_year, cutoff_year - 1, -1))
        if max_needed > 600
        else [None]
    )
    max_pages_per_slice = min(650, max(2, (max_needed // 10) + 2))
    batch_size = 10
    print(f"[Detik Search] Mengambil arsip Detik untuk '{keyword}' ({len(year_slices)} rentang)...", flush=True)

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        for yr in year_slices:
            if len(results) >= max_needed:
                break
            yr_label = str(yr) if yr else "terkini"
            stale_batches = 0
            for start_p in range(1, max_pages_per_slice + 1, batch_size):
                if len(results) >= max_needed:
                    break
                prev_len = len(results)
                end_p = min(start_p + batch_size - 1, max_pages_per_slice)
                pages = list(range(start_p, end_p + 1))
                batch_outputs = list(executor.map(lambda p: _fetch_detik_page(keyword, p, year_range, yr), pages))
                batch_outputs.sort(key=lambda x: x["page"])

                stop_slice = False
                for out in batch_outputs:
                    if out["empty"]:
                        stop_slice = True
                        break
                    for item in out["items"]:
                        cu = canonicalize_url(item["url"])
                        if cu in seen_urls:
                            continue
                        seen_urls.add(cu)
                        results.append(item)
                        if len(results) >= max_needed:
                            stop_slice = True
                            break
                    if stop_slice or out["cutoff"]:
                        stop_slice = True
                        break

                if len(results) > prev_len and (start_p == 1 or ((start_p - 1) // batch_size) % 3 == 0):
                    print(f"[Detik Search {yr_label}] Hal {start_p}-{end_p}: total {len(results)} artikel", flush=True)
                stale_batches = 0 if len(results) > prev_len else (stale_batches + 1)
                if stop_slice or stale_batches >= 2:
                    break
    print(f"[Detik Search] Total selesai: {len(results)} artikel.", flush=True)
    return results


def _fetch_kompas_page(keyword: str, page_num: int, year_range: int) -> Dict[str, Any]:
    """Ambil dan parse satu halaman pencarian Kompas.com (20 artikel/halaman)."""
    page_items: List[Dict[str, Any]] = []
    try:
        r = requests.get(
            "https://search.kompas.com/search",
            params={"q": keyword, "page": str(page_num)},
            headers={"User-Agent": UA},
            timeout=(5, 8),
        )
        if r.status_code != 200:
            return {"page": page_num, "items": [], "empty": True, "cutoff": False}
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".articleList .articleItem")
        if not cards:
            return {"page": page_num, "items": [], "empty": True, "cutoff": False}

        hit_cutoff = False
        for card in cards:
            a = card.select_one("a.article-link[href], a[href]")
            if not a:
                continue
            art_url = (a.get("href") or "").strip()
            if not art_url.startswith("http"):
                continue
            t_el = card.select_one(".articleTitle")
            title = t_el.get_text(" ", strip=True) if t_el else ""
            lead_el = card.select_one(".articleLead p, .articleLead")
            desc = lead_el.get_text(" ", strip=True) if lead_el else ""
            if not title or is_spam_or_judol(desc, title, art_url):
                continue
            if not matches_keyword(f"{title} {desc} {art_url}", keyword):
                continue
            dt_el = card.select_one(".articlePost-date")
            raw_date = dt_el.get_text(" ", strip=True) if dt_el else ""
            dt = _parse_indonesian_date(raw_date)
            if not is_within_years(dt, year_range):
                hit_cutoff = True
                break
            sub_el = card.select_one(".articlePost-subtitle")
            channel = f"Kompas ({sub_el.get_text(' ', strip=True)})" if sub_el else "kompas.com"
            img = card.select_one("img")
            thumb = (img.get("src") or img.get("data-src") or "") if img else ""
            page_items.append(_build_news_item(
                id_prefix="gdelt_kompas",
                keyword=keyword,
                title=title,
                content=desc or f"{title} — Liputan Kompas.com ({dt.strftime('%Y-%m-%d')}).",
                url=art_url,
                thumb=thumb,
                source=channel,
                dt=dt,
                raw_data={"source": "kompas_search", "raw_date": raw_date},
            ))
        return {"page": page_num, "items": page_items, "empty": False, "cutoff": hit_cutoff}
    except Exception:
        return {"page": page_num, "items": [], "empty": False, "cutoff": False}


def _scrape_kompas_search(keyword: str, max_needed: int, year_range: int, seen_urls: set) -> List[Dict[str, Any]]:
    """Ambil arsip berita Kompas.com secara paralel per batch."""
    results: List[Dict[str, Any]] = []
    max_pages = min(160, max(2, (max_needed // 20) + 2))
    batch_size = 10
    print(f"[Kompas Search] Mengambil arsip Kompas untuk '{keyword}' (maks {max_pages} halaman)...", flush=True)

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        stale_batches = 0
        for start_p in range(1, max_pages + 1, batch_size):
            if len(results) >= max_needed:
                break
            prev_len = len(results)
            end_p = min(start_p + batch_size - 1, max_pages)
            pages = list(range(start_p, end_p + 1))
            batch_outputs = list(executor.map(lambda p: _fetch_kompas_page(keyword, p, year_range), pages))
            batch_outputs.sort(key=lambda x: x["page"])

            stop_crawling = False
            for out in batch_outputs:
                if out["empty"]:
                    stop_crawling = True
                    break
                for item in out["items"]:
                    cu = canonicalize_url(item["url"])
                    if cu in seen_urls:
                        continue
                    seen_urls.add(cu)
                    results.append(item)
                    if len(results) >= max_needed:
                        stop_crawling = True
                        break
                if stop_crawling or out["cutoff"]:
                    stop_crawling = True
                    break

            print(f"[Kompas Search] Halaman {start_p}-{end_p}: terkumpul {len(results)} artikel", flush=True)
            stale_batches = 0 if len(results) > prev_len else (stale_batches + 1)
            if stop_crawling or stale_batches >= 2:
                break
    return results


def _fetch_antara_page(keyword: str, page_num: int, year_range: int) -> List[Dict[str, Any]]:
    """Ambil dan parse artikel hasil pencarian AntaraNews (ketat filter kecocokan keyword)."""
    items: List[Dict[str, Any]] = []
    try:
        r = requests.get(
            "https://www.antaranews.com/search",
            params={"q": keyword, "page": str(page_num)},
            headers={"User-Agent": UA},
            timeout=(5, 8),
        )
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select(".card__post"):
            a = card.select_one("h2 a[href], .card__post__title a[href], a[href]")
            if not a:
                continue
            art_url = (a.get("href") or "").strip()
            if not art_url.startswith("http"):
                continue
            title = (a.get("title") or a.get_text(" ", strip=True)).strip()
            p_el = card.select_one("p")
            desc = p_el.get_text(" ", strip=True) if p_el else ""
            if not title or not matches_keyword(f"{title} {desc} {art_url}", keyword) or is_spam_or_judol(desc, title, art_url):
                continue
            dt_el = card.select_one(".list-inline-item span, time, .card__post__author-info span")
            raw_date = dt_el.get_text(" ", strip=True) if dt_el else ""
            dt = _parse_indonesian_date(raw_date)
            if not is_within_years(dt, year_range):
                continue
            img = card.select_one("img")
            thumb = (img.get("data-src") or img.get("src") or "") if img else ""
            items.append(_build_news_item(
                id_prefix="gdelt_antara",
                keyword=keyword,
                title=title,
                content=desc or f"{title} — ANTARA News ({dt.strftime('%Y-%m-%d')}).",
                url=art_url,
                thumb=thumb,
                source="antaranews.com",
                dt=dt,
                raw_data={"source": "antara_search", "raw_date": raw_date},
            ))
    except Exception:
        pass
    return items


def _scrape_antara_search(keyword: str, max_needed: int, year_range: int, seen_urls: set) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    max_pages = min(120, max(2, (max_needed // 10) + 1))
    batch_size = 8
    print(f"[Antara Search] Mengambil arsip AntaraNews untuk '{keyword}' (maks {max_pages} halaman)...", flush=True)
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        stale_batches = 0
        for start_p in range(1, max_pages + 1, batch_size):
            if len(results) >= max_needed:
                break
            prev_len = len(results)
            end_p = min(start_p + batch_size - 1, max_pages)
            for batch_items in executor.map(lambda p: _fetch_antara_page(keyword, p, year_range), range(start_p, end_p + 1)):
                for item in batch_items:
                    cu = canonicalize_url(item["url"])
                    if cu in seen_urls:
                        continue
                    seen_urls.add(cu)
                    results.append(item)
                    if len(results) >= max_needed:
                        return results
            stale_batches = 0 if len(results) > prev_len else (stale_batches + 1)
            if stale_batches >= 2:
                break
    print(f"[Antara Search] Total selesai: {len(results)} artikel.", flush=True)
    return results


def _scrape_indonesian_rss(keyword: str, max_needed: int, year_range: int, seen_urls: set) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    feeds = [
        ("antaranews.com", "https://www.antaranews.com/rss/terkini.xml"),
        ("cnnindonesia.com", "https://www.cnnindonesia.com/nasional/rss"),
        ("cnbcindonesia.com", "https://www.cnbcindonesia.com/news/rss"),
    ]
    for domain, feed_url in feeds:
        if len(results) >= max_needed:
            break
        try:
            r = requests.get(feed_url, headers={"User-Agent": UA}, timeout=10)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                desc_html = item.findtext("description") or ""
                desc = BeautifulSoup(desc_html, "html.parser").get_text(" ", strip=True)
                if not link or is_spam_or_judol(desc, title, link):
                    continue
                cu = canonicalize_url(link)
                if cu in seen_urls:
                    continue
                if not matches_keyword(f"{title} {desc}", keyword):
                    continue
                pub_raw = item.findtext("pubDate") or ""
                try:
                    dt = parsedate_to_datetime(pub_raw) if pub_raw else datetime.now(timezone.utc)
                except Exception:
                    dt = datetime.now(timezone.utc)
                if not is_within_years(dt, year_range):
                    continue
                enc = item.find("enclosure")
                img = enc.attrib.get("url", "") if enc is not None else ""
                if not img:
                    m_img = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_html)
                    img = m_img.group(1) if m_img else ""
                seen_urls.add(cu)
                results.append(_build_news_item(
                    id_prefix="gdelt_rss",
                    keyword=keyword,
                    title=title,
                    content=desc[:500] or title,
                    url=link,
                    thumb=img,
                    source=domain,
                    dt=dt,
                    raw_data={"rss_feed": feed_url},
                ))
                if len(results) >= max_needed:
                    break
        except Exception as e:
            print(f"[RSS News] Error {domain}: {e}")
    return results


def scrape_gdelt(keyword: str = "karhutla", max_records: int = 30, timespan: str = "5y") -> List[Dict[str, Any]]:
    year_match = re.match(r"(\d+)y", (timespan or "5y").lower())
    year_range = int(year_match.group(1)) if year_match else 5
    seen_urls: set = set()
    results: List[Dict[str, Any]] = []

    results.extend(_scrape_gdelt_api(keyword, max_records, timespan, seen_urls))

    if len(results) < max_records:
        results.extend(_scrape_gdelt_master_feeds(keyword, max_records - len(results), year_range, seen_urls))

    if len(results) < max_records:
        results.extend(_scrape_detik_search(keyword, max_records - len(results), year_range, seen_urls))

    if len(results) < max_records:
        results.extend(_scrape_kompas_search(keyword, max_records - len(results), year_range, seen_urls))

    if len(results) < max_records:
        results.extend(_scrape_antara_search(keyword, max_records - len(results), year_range, seen_urls))

    if len(results) < max_records:
        results.extend(_scrape_indonesian_rss(keyword, max_records - len(results), year_range, seen_urls))

    return results[:max_records]


def get_gdelt_timeline_data(keyword: str = "karhutla", timespan: str = "30d") -> Dict[str, Any]:
    timeline_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    output: Dict[str, Any] = {"keyword": keyword, "vol_timeline": [], "tone_timeline": []}
    for mode, key in [("TimelineVolRaw", "vol_timeline"), ("TimelineTone", "tone_timeline")]:
        try:
            resp = requests.get(
                timeline_url,
                params={"query": keyword, "mode": mode, "format": "json", "timespan": timespan},
                headers={"User-Agent": UA},
                timeout=10,
            )
            if resp.status_code == 200:
                output[key] = resp.json().get("timeline", [])
        except Exception as e:
            print(f"[GDELT Timeline] Error {mode}: {e}")
    return output
