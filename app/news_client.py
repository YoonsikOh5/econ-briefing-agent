import feedparser
from typing import List, Dict

RSS_SOURCES = [
    ("hankyung_econ", "https://www.hankyung.com/feed/economy"),
    ("hani_econ", "https://www.hani.co.kr/rss/economy/"),
]

def fetch_rss_items(limit_per_source: int = 10) -> List[Dict]:
    items: List[Dict] = []
    for source, url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for e in feed.entries[:limit_per_source]:
            title = getattr(e, "title", "") or ""
            link = getattr(e, "link", "") or ""
            summary = getattr(e, "summary", "") or ""
            summary = summary.strip()[:350]

            if not title.strip() or not link.strip():
                continue

            items.append({
                "source": source,
                "title": title.strip(),
                "link": link.strip(),
                "summary": summary,
                "published": getattr(e, "published", "") or getattr(e, "updated", ""),
            })
    return items
