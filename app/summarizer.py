import json
import asyncio
from openai import OpenAI

client = OpenAI()

def _extract_output_text(resp) -> str:
    txt = (getattr(resp, "output_text", "") or "").strip()
    if txt:
        return txt
    parts = []
    for item in getattr(resp, "output", []) or []:
        for c in getattr(item, "content", []) or []:
            t = getattr(c, "text", None)
            if isinstance(t, str) and t.strip():
                parts.append(t.strip())
    return "\n".join(parts).strip()

async def generate_top3_news_briefing_openai(news_items: list[dict]) -> str:
    system = (
        "You are a Korean business briefing writer.\n"
        "Goal: Create a KakaoTalk-friendly morning economics briefing.\n"
        "Use ONLY provided items (title, link, summary). Do not invent facts.\n"
        "No Chinese. No English.\n"
        "\n"
        "Output MUST follow this exact format:\n"
        "## 알아두면 쓸데있는 오늘의 경제뉴스 ##\n\n"
        "1. [제목](링크)\n"
        "   - 요약: ... (2 sentences)\n"
        "...\n"
        "\n"
        "Rules:\n"
        "- Exactly 3 items.\n"
        "- Each '요약' is TWO sentence.\n"
        "- Keep it concise.\n"
    )

    user_payload = {"items": news_items}

    def _call():
        return client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            max_output_tokens=520,
            store=False,
            text={"format": {"type": "text"}},
        )

    resp = await asyncio.to_thread(_call)
    text = _extract_output_text(resp)
    if not text:
        raise RuntimeError("Empty briefing text from model")
    return text
