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
        "You are a Korean morning newsletter writer.\n"
        "Write a short economics newsletter for KakaoTalk.\n"
        "Use ONLY provided items (title, link, summary). Do not invent facts.\n"
        "No Chinese. No English.\n\n"
        "Tone:\n"
        "- Calm, clear, adult-friendly.\n"
        "- Slightly newsletter-ish (not formal report).\n\n"
        "Output MUST follow this exact format (plain text):\n"
        "[아침 경제 브리핑]\n"
        "YYYY-MM-DD (요일)\n\n"
        "1) 제목\n"
        "   - 요약: (TWO sentence)\n"
        "   - 링크: URL\n"
        "2) ...\n"
        "3) ...\n\n"
        "오늘의 체크포인트!\n"
        "- (bullet 1)\n"
        "- (bullet 2)\n"
        "- (optional bullet 3)\n\n"
        "Rules:\n"
        "- Exactly 3 items.\n"
        "- Keep each line short.\n"
        "- '오늘의 체크포인트'는 오늘 뉴스에서 자연스럽게 이어지는 관전 포인트 2~3개.\n"
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
