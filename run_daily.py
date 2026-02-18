import os
import asyncio

from app.news_client import fetch_rss_items, filter_items_by_kst_date, filter_items_recent_hours
from app.briefing_quality import dedup_by_title, select_top_items, diversify_by_source
from app.summarizer import generate_top3_news_briefing_openai
from app.kakao_client import send_to_me_text_multi, send_to_friend_uuid_multi
from datetime import datetime
from zoneinfo import ZoneInfo


def _env(name: str, required: bool = True) -> str:
    v = os.getenv(name, "").strip()
    if required and not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v

async def main():
    _env("OPENAI_API_KEY")
    _env("KAKAO_ACCESS_TOKEN")
    _env("KAKAO_REFRESH_TOKEN")
    _env("KAKAO_REST_API_KEY")
    _env("KAKAO_CLIENT_SECRET")

    friend_uuid = _env("KAKAO_FRIEND_UUID", required=False)

    date_kst = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

    items = fetch_rss_items(limit_per_source=12)

    # 1) Today only
    today_items = filter_items_by_kst_date(items, date_kst)

    # 2) Fallback if too few
    # TOP3라면 최소 3개는 필요하니까, 3개 미만이면 48h → 그래도 부족하면 72h
    if len(today_items) < 3:
        today_items = filter_items_recent_hours(items, hours=48)
    if len(today_items) < 3:
        today_items = filter_items_recent_hours(items, hours=72)

    # 이제부터는 이 today_items로 quality preprocessing
    items = dedup_by_title(today_items, threshold=0.88)
    items = select_top_items(items, top_n=8)
    items = diversify_by_source(items, per_source_cap=3)

    briefing = await generate_top3_news_briefing_openai(items, date_kst)

    await send_to_me_text_multi(briefing)
    if friend_uuid:
        await send_to_friend_uuid_multi(friend_uuid, briefing)

    print("DONE")

if __name__ == "__main__":
    asyncio.run(main())
