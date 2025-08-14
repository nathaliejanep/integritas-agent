import json
from app.adapters.asi_client import ASIClient
from app.schemas.chat import IntentResult

class IntentService:
    def __init__(self, asi: ASIClient):
        self.asi = asi

    async def detect(self, text: str) -> IntentResult:
        content = await self.asi.classify_intent(text)
        kind = "GENERAL"
        payload = {}

        if content.startswith("STAMP_HASH:"):
            kind = "STAMP_HASH"
            payload = {"hash": content.split("STAMP_HASH:", 1)[1].strip()}
        elif content.startswith("VERIFY_PROOF:"):
            kind = "VERIFY_PROOF"
            raw = content.split("VERIFY_PROOF:", 1)[1].strip()
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"_raw": raw, "_error": "Invalid JSON from LLM"}
        return IntentResult(kind=kind, payload=payload, raw_response=content)
