import asyncio
from datetime import datetime, timezone
from app.adapters.integritas_client import IntegritasClient
from app.config.settings import POLL_DELAY_SECONDS, POLL_MAX_ATTEMPTS

class StampingService:
    def __init__(self, integ: IntegritasClient):
        self.integ = integ

    async def stamp(self, hash_value: str, request_id: str) -> str | None:
        return await self.integ.stamp_hash(hash_value, request_id)

    async def wait_for_onchain(self, uid: str, attempts: int = POLL_MAX_ATTEMPTS, delay: int = POLL_DELAY_SECONDS, status_callback=None):
        for attempt in range(attempts):
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
            
            # Send status update if callback provided and not the first attempt
            if status_callback and attempt > 0:
                await status_callback(f"⏳ Still checking blockchain confirmation... (attempt {attempt + 1}/{attempts})")
            
            await asyncio.sleep(delay)

        return {"onchain": False, "proof": "", "root": "", "address": "", "data": ""}

    async def stamp_hash(self, hash_value: str, sender: str, request_id: str = None, status_callback=None) -> dict:
        """
        Complete hash stamping workflow including validation, stamping, and on-chain confirmation.
        
        Args:
            hash_value: The hash to stamp
            sender: The sender identifier (used for request_id generation if not provided)
            request_id: Optional request ID, will be generated if not provided
            status_callback: Optional callback function to send intermediate status messages
            
        Returns:
            dict: Result containing success status, messages, and proof data
        """
        # Validate hash
        if len(hash_value) < 32:
            return {
                "success": False,
                "message": "The provided value doesn't look like a valid hash. Make sure you're using the correct hash value of a sha3-256 hash.",
                "uid": None,
                "proof": None
            }
        
        # Generate request_id if not provided
        if not request_id:
            request_id = f"chat-{sender[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
        
        # Stamp the hash
        uid = await self.stamp(hash_value, request_id)
        if not uid:
            return {
                "success": False,
                "message": "❌ Failed to stamp hash. Please check the hash and try again.",
                "uid": None,
                "proof": None
            }
        
        # Send intermediate status message if callback provided
        if status_callback:
            await status_callback(f"✅ Hash stamped successfully!\n\n**UID:** {uid}\n\nChecking on‑chain confirmation...")
        
        # Wait for on-chain confirmation
        onchain = await self.wait_for_onchain(uid, status_callback=status_callback)
        
        if onchain["onchain"]:
            proof = {
                "proof": onchain["proof"],
                "address": onchain["address"],
                "root": onchain["root"],
                "data": onchain["data"],
            }
            return {
                "success": True,
                "message": "✅ Hash stamped successfully!",
                "uid": uid,
                "proof": proof,
                "onchain": True
            }
        else:
            return {
                "success": True,
                "message": f"⏳ Status Update\n\n**UID:** {uid}\nStill waiting for blockchain confirmation.",
                "uid": uid,
                "proof": None,
                "onchain": False
            }
        # else:
        #     return {
        #         "success": True,
        #         "message": f"⏳ Status Update\n\n**UID:** {uid}\nStill waiting for blockchain confirmation.",
        #         "uid": uid,
        #         "proof": None,
        #         "onchain": False
        #     }
