from __future__ import annotations
from typing import List, Dict, Tuple
import re

def _normalize_title(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[\"'“”‘’]", "", t)
    return t

def dedup_by_title(items: List[Dict], threshold: float = 0.88) -> List[Dict]:
    def jaccard(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    kept: List[Dict] = []
    kept_sets: List[set] = []

    for it in items:
        title = _normalize_title(it.get("title", ""))
        tokens = set(title.split())
        if not tokens:
            continue

        dup = False
        for s in kept_sets:
            if jaccard(tokens, s) >= threshold:
                dup = True
                break

        if not dup:
            kept.append(it)
            kept_sets.append(tokens)

    return kept

_KEYWORD_WEIGHTS: List[Tuple[str, int]] = [
    ("금리", 5), ("기준금리", 6), ("연준", 5), ("fomc", 5),
    ("환율", 5), ("달러", 4), ("usd", 4),
    ("물가", 5), ("인플레이션", 5), ("cpi", 5),
    ("반도체", 4), ("엔비디아", 4), ("삼성", 3), ("하이닉스", 3),
    ("코스피", 4), ("코스닥", 3), ("증시", 4),
    ("부동산", 3), ("대출", 3),
    ("중국", 3), ("미국", 3), ("일본", 2), ("유럽", 2),
]

def score_item(item: Dict) -> int:
    text = f"{item.get('title','')} {item.get('summary','')}".lower()
    score = 0
    for kw, w in _KEYWORD_WEIGHTS:
        if kw in text:
            score += w
    score += min(len(item.get("summary","")) // 200, 2)
    return score

def select_top_items(items: List[Dict], top_n: int = 8) -> List[Dict]:
    scored = [(score_item(it), it) for it in items]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scored[:top_n]]

def diversify_by_source(items: List[Dict], per_source_cap: int = 3) -> List[Dict]:
    out: List[Dict] = []
    counts = {}
    for it in items:
        src = it.get("source", "unknown")
        counts.setdefault(src, 0)
        if counts[src] >= per_source_cap:
            continue
        out.append(it)
        counts[src] += 1
    return out
