import io
import json
import httpx
from typing import Dict, Any, List, Optional
from app.config.settings import INTEGRITAS_API_KEY, INTEGRITAS_BASE_URL

class IntegritasClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=INTEGRITAS_BASE_URL,
            headers={"x-api-key": INTEGRITAS_API_KEY},
            timeout=600
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

    async def get_proof_file(self, uids: list[str], filename: Optional[str] = None) -> str:
        """
        Download proof file for given UIDs from /v1/timestamp/get-proof-file endpoint.
        
        Args:
            uids: List of UIDs to get proof file for
            filename: Optional custom filename, if not provided will use server suggestion or default
            
        Returns:
            str: Path to the saved proof file
            
        Raises:
            RuntimeError: If the API request fails
        """
        r = await self._client.post(
            "/v1/timestamp/get-proof-file",
            headers={"Content-Type": "application/json"},
            json={"uids": uids},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Failed to fetch proof file: {r.status_code} {r.text}")

        # Try to get filename from Content-Disposition header
        cd = r.headers.get("content-disposition", "")
        if not filename and "filename=" in cd:
            # Parse filename from header: filename="foo.json"
            start = cd.find('filename="') + len('filename="')
            end = cd.find('"', start)
            filename = cd[start:end] if start > -1 and end > -1 else None

        if not filename:
            # Generate default filename with timestamp
            from datetime import datetime, timezone
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%fZ")[:-3] + "Z"
            filename = f"proof-file-{timestamp}.json"

        # Save the file
        with open(filename, "wb") as f:
            f.write(r.content)

        return filename
        
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
