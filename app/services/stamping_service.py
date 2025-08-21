import asyncio
from datetime import datetime, timezone
from app.adapters.integritas_client import IntegritasClient
from app.config.settings import POLL_DELAY_SECONDS, POLL_MAX_ATTEMPTS

class StampingService:
    def __init__(self, integ: IntegritasClient):
        self.integ = integ

    async def stamp(self, hash_value: str, request_id: str) -> str | None:
        return await self.integ.stamp_hash(hash_value, request_id)

    async def wait_for_onchain(self, uid: str, attempts: int = POLL_MAX_ATTEMPTS, delay: int = POLL_DELAY_SECONDS):
        for _ in range(attempts):
            data = await self.integ.status_by_uids([uid])
            if not data or data.get("status") != "success":
                return {"onchain": False, "proof": "", "root": "", "address": "", "data": ""}

            item = data["data"][0]
            if item.get("onchain", False):
                return {
                    "onchain": True,
                    "proof": item.get("proof", ""),
                    "root": item.get("root", ""),
                    "address": item.get("address", ""),
                    "data": item.get("data", "")
                }
            await asyncio.sleep(delay)

        return {"onchain": False, "proof": "", "root": "", "address": "", "data": ""}
