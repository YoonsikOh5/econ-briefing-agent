import os
import json
import asyncio
import httpx
from typing import List

KAKAO_API = "https://kapi.kakao.com"
SEND_TO_ME_URL = f"{KAKAO_API}/v2/api/talk/memo/default/send"
SEND_TO_FRIENDS_URL = f"{KAKAO_API}/v1/api/talk/friends/message/default/send"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"

def _env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v

async def refresh_access_token() -> str:
    rest_key = _env("KAKAO_REST_API_KEY")
    refresh_token = _env("KAKAO_REFRESH_TOKEN")
    client_secret = os.getenv("KAKAO_CLIENT_SECRET", "").strip()

    data = {
        "grant_type": "refresh_token",
        "client_id": rest_key,
        "refresh_token": refresh_token,
    }
    if client_secret:
        data["client_secret"] = client_secret

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(TOKEN_URL, data=data)
        r.raise_for_status()
        obj = r.json()

    new_access = obj.get("access_token")
    if not new_access:
        raise RuntimeError(f"Refresh failed: {obj}")
    return new_access

def split_for_kakao(text: str, limit: int = 900) -> List[str]:
    text = text.strip()
    if len(text) <= limit:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    cur = ""

    def push():
        nonlocal cur
        if cur.strip():
            chunks.append(cur.strip())
        cur = ""

    for p in paragraphs:
        if cur and len(cur) + 2 + len(p) > limit:
            push()

        if len(p) > limit:
            lines = [ln for ln in p.split("\n") if ln.strip()]
            for ln in lines:
                if cur and len(cur) + 1 + len(ln) > limit:
                    push()
                cur = (cur + "\n" + ln).strip() if cur else ln
            push()
            continue

        cur = (cur + "\n\n" + p).strip() if cur else p

    push()
    return chunks

async def _post_form(url: str, token: str, data: dict) -> httpx.Response:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        return await client.post(url, headers=headers, data=data)

async def send_to_me_text(message: str) -> None:
    access = _env("KAKAO_ACCESS_TOKEN")

    template_object = {
        "object_type": "text",
        "text": message[:950],
        "link": {"web_url": "https://www.hankyung.com/", "mobile_web_url": "https://www.hankyung.com/"},
        "button_title": "영어뉴스도 한번?",
    }
    data = {"template_object": json.dumps(template_object, ensure_ascii=False)}

    r = await _post_form(SEND_TO_ME_URL, access, data)
    if r.status_code == 401:
        access = await refresh_access_token()
        r = await _post_form(SEND_TO_ME_URL, access, data)

    if r.status_code != 200:
        raise RuntimeError(f"Kakao send-to-me error {r.status_code}: {r.text}")

async def send_to_friend_uuid(receiver_uuid: str, message: str) -> None:
    access = _env("KAKAO_ACCESS_TOKEN")

    template_object = {
        "object_type": "text",
        "text": message[:950],
        "link": {"web_url": "https://www.hankyung.com/", "mobile_web_url": "https://www.hankyung.com/"},
        "button_title": "영어뉴스도 한번?",
    }
    data = {
        "receiver_uuids": json.dumps([receiver_uuid]),
        "template_object": json.dumps(template_object, ensure_ascii=False),
    }

    r = await _post_form(SEND_TO_FRIENDS_URL, access, data)
    if r.status_code == 401:
        access = await refresh_access_token()
        r = await _post_form(SEND_TO_FRIENDS_URL, access, data)

    if r.status_code != 200:
        raise RuntimeError(f"Kakao send-to-friend error {r.status_code}: {r.text}")

async def send_to_me_text_multi(text: str) -> List[str]:
    chunks = split_for_kakao(text, limit=900)
    for chunk in chunks:
        await send_to_me_text(chunk)
        await asyncio.sleep(0.3)
    return chunks

async def send_to_friend_uuid_multi(receiver_uuid: str, text: str) -> List[str]:
    chunks = split_for_kakao(text, limit=900)
    for chunk in chunks:
        await send_to_friend_uuid(receiver_uuid, chunk)
        await asyncio.sleep(0.3)
    return chunks
