import io
import json
import httpx
from typing import Dict, Any, List
from app.config.settings import INTEGRITAS_API_KEY, INTEGRITAS_BASE_URL

class IntegritasClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=INTEGRITAS_BASE_URL,
            headers={"x-api-key": INTEGRITAS_API_KEY},
            timeout=30
        )

    async def stamp_hash(self, hash_value: str, request_id: str) -> str | None:
        r = await self._client.post(
            "/v1/timestamp/post",
            headers={"x-request-id": request_id, "Content-Type": "application/json"},
            json={"hash": hash_value}
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("status") == "success":
            return data.get("data", {}).get("uid")
        return None

    async def status_by_uids(self, uids: list[str]) -> Dict[str, Any] | None:
        r = await self._client.post(
            "/v1/timestamp/status",
            headers={"Content-Type": "application/json"},
            json={"uids": uids}
        )
        if r.status_code != 200:
            return None
        return r.json()

    async def verify_proof(self, items: list[dict], request_id: str) -> Dict[str, Any] | None:
        # Server expects a JSON file upload. Send in-memory file.
        bytes_data = json.dumps(items).encode("utf-8")
        files = {"file": ("proof_data.json", io.BytesIO(bytes_data), "application/json")}
        r = await self._client.post(
            "/v1/verify/post-lite",
            headers={"x-request-id": request_id, "x-report-required": "true"},
            files=files
        )
        if r.status_code != 200:
            return None
        return r.json()

    async def aclose(self):
        await self._client.aclose()
