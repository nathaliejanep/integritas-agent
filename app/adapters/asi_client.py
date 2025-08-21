import httpx
from typing import List, Dict
from app.config.settings import ASI_API_KEY, SUBJECT_MATTER

ASI_BASE = "https://api.asi1.ai/v1"

class ASIClient:
    def __init__(self):
        self._client = httpx.AsyncClient(base_url=ASI_BASE, headers={
            "Authorization": f"Bearer {ASI_API_KEY}",
            "Content-Type": "application/json",
        }, timeout=30)

    async def classify_intent(self, user_text: str) -> str:
        payload = {
            "model": "asi1-mini",
            "messages": [
                {"role":"system","content": f"You are an expert assistant specializing in {SUBJECT_MATTER}"},
                {"role":"user","content": user_text}
            ],
            "max_tokens": 2048
        }
        r = await self._client.post("/chat/completions", json=payload)
        r.raise_for_status()
        data = r.json()
        return str(data["choices"][0]["message"]["content"])

    async def explain_verification(self, docs: str, reason_payload: str) -> str:
        # Reuse same endpoint; different prompt specialization
        messages = [
            {"role":"system","content": f"""
You analyze blockchain verification results.
Docs: {docs}
Summarize verification in natural language, highlight the on‑chain date (if available).
No links. Polite, concise, structured. 3–4 sections with short headings and icons. Make sure the headings are marked as headings and the paragrapghs are not bold or marked as headings. Make sure every paragraph is formatted the same way.
"""},
            {"role":"assistant","content": f"Please explain: {reason_payload}. Skip introductions."}
        ]
        r = await self._client.post("/chat/completions", json={
            "model":"asi1-mini", "messages": messages, "max_tokens": 2048
        })
        r.raise_for_status()
        data = r.json()
        return str(data["choices"][0]["message"]["content"])

    async def aclose(self):
        await self._client.aclose()
