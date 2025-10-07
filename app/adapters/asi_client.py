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
            {"role":"system","content": """
                You are an expert blockchain verification analyst. Your task is to explain verification results based on the provided documentation.

                CRITICAL: You must ONLY use information that is explicitly provided in the verification results. NEVER make up, assume, or infer any information that is not directly stated in the results.

                Your response should:
                - Summarize the verification results in natural language
                - Highlight the on-chain date if available, always use the date from the verification result and never make up a date
                - Be structured with 2-3 clear sections
                - Each section should be a single sentence.
                - Be polite, concise, and factual
                - Include no external links or references

                IMPORTANT: If any information is not explicitly stated in the verification results, do not include it in your response. Stick strictly to the facts provided.
                IMPORTANT: Use only the JSON data from the API response. Do not analyze or base your answers on the PDF file. Stick strictly to the facts provided.
            """},
            {"role":"user","content": f"Based on these verification results: {docs}\n\nPlease explain: {reason_payload}\n\nIMPORTANT: Only use information from the verification results above. Do not make up or assume any information."}
        ]
        r = await self._client.post("/chat/completions", json={
            "model":"asi1-mini", 
            "messages": messages, 
            "max_tokens": 2048,
            "temperature": 0.1,  # Lower temperature for more factual responses
            "top_p": 0.9,       # Focus on most likely tokens
            "frequency_penalty": 0.1,  # Reduce repetition
            "presence_penalty": 0.1    # Encourage focus on provided content
        })
        r.raise_for_status()
        data = r.json()
        return str(data["choices"][0]["message"]["content"])

    async def aclose(self):
        await self._client.aclose()
