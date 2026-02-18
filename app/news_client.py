import feedparser
from typing import List, Dict
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import time as _time

RSS_SOURCES = [
    ("hankyung_econ", "https://www.hankyung.com/feed/economy"),
    ("hani_econ", "https://www.hani.co.kr/rss/economy/"),
    ("mk_econ", "https://www.mk.co.kr/rss/30100041/")
]

def _to_utc_dt(entry) -> datetime | None:
    """
    Convert feedparser entry published_parsed/updated_parsed to UTC datetime.
    """
    st = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if st is None:
        return None
    # published_parsed is typically in UTC already; treat as UTC
    return datetime.fromtimestamp(_time.mktime(st), tz=timezone.utc)

def fetch_rss_items(limit_per_source: int = 10) -> List[Dict]:
    items: List[Dict] = []
    for source, url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for e in feed.entries[:limit_per_source]:
            title = (getattr(e, "title", "") or "").strip()
            link = (getattr(e, "link", "") or "").strip()
            summary = (getattr(e, "summary", "") or "").strip()[:350]

            if not title or not link:
                continue

            published_dt_utc = _to_utc_dt(e)

            items.append({
                "source": source,
                "title": title,
                "link": link,
                "summary": summary,
                "published": getattr(e, "published", "") or getattr(e, "updated", ""),
                "published_dt_utc": published_dt_utc.isoformat() if published_dt_utc else None,
            })
    return items

KST = ZoneInfo("Asia/Seoul")

def filter_items_by_kst_date(items: List[Dict], date_kst: str) -> List[Dict]:
    """
    Keep items whose published_dt_utc falls on the given KST date.
    date_kst: 'YYYY-MM-DD'
    """
    target = datetime.strptime(date_kst, "%Y-%m-%d").replace(tzinfo=KST).date()

    out = []
    for it in items:
        iso = it.get("published_dt_utc")
        if not iso:
            continue  # if no timestamp, drop for "today-only" mode
        dt_utc = datetime.fromisoformat(iso)
        dt_kst = dt_utc.astimezone(KST)
        if dt_kst.date() == target:
            out.append(it)
    return out

def filter_items_recent_hours(items: List[Dict], hours: int = 48) -> List[Dict]:
    """
    Fallback: keep items within the last N hours (KST/UTC independent).
    """
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=hours)

    out = []
    for it in items:
        iso = it.get("published_dt_utc")
        if not iso:
            continue
        dt_utc = datetime.fromisoformat(iso)
        if dt_utc >= cutoff:
            out.append(it)
    return out