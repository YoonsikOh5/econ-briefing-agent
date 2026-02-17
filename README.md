# econ-briefing-agent (GitHub Actions)

A serverless daily runner that:
1) Fetches RSS economics news
2) Dedups + scores + diversifies
3) Generates TOP3 Kakao-friendly briefing using OpenAI
4) Sends to KakaoTalk (me + optional friend)

## Setup
1) Create a GitHub repo and upload this folder as-is.
2) Add GitHub Secrets:
   - OPENAI_API_KEY
   - KAKAO_ACCESS_TOKEN
   - KAKAO_REFRESH_TOKEN
   - KAKAO_REST_API_KEY
   - KAKAO_CLIENT_SECRET
   - KAKAO_FRIEND_UUID (optional)

## Schedule
KST 07:00 = UTC 22:00
Cron in .github/workflows/daily.yml: 0 22 * * *
