import asyncio
import json
from uagents import Agent, Context, Model
from typing import Literal, Optional
from uuid import uuid4

# ----- Common -----
class Error(Model):
    code: Literal["BAD_REQUEST","UNAUTHORIZED","NOT_FOUND","TIMEOUT","INTERNAL"]
    message: str

class BaseRequest(Model):
    request_id: str

class BaseResponse(Model):
    request_id: str
    ok: bool
    error: Optional[Error] = None

# ----- Stamp Hash -----
class StampHashRequest(BaseRequest):
    hash: str

class StampHashResponse(BaseResponse):
    uid: Optional[str] = None  # set when ok=True

# ----- Status Check -----
class UidRequest(BaseRequest):
    uid: str

class UidResponse(BaseResponse):
    proof: Optional[str] = None
    root: Optional[str] = None
    address: Optional[str] = None
    data: Optional[str] = None

INTEGRITAS_AGENT_ADDRESS = "agent1q2svq8ukmatt8edfpp4heckcmxpk7gchelecf2v98pf723w932dsst7059g"

# -----------------------
# Config
# -----------------------
consumer = Agent()

# ENTER THE HASH YOU WISH TO STAMP HERE
HASH_TO_SEND = ""

# -----------------------
# Handlers
# -----------------------
@consumer.on_message(StampHashResponse)
async def on_stamp_resp(ctx: Context, sender: str, msg: StampHashResponse):
    payload = msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
    payload_s = json.dumps(payload, ensure_ascii=False)

    if msg.ok and msg.uid:
        ctx.logger.info(f"Stamp success ✅ uid={msg.uid}")
        # Optional: immediately ask for on-chain status (fire-and-forget)
        await ctx.send(sender, UidRequest(request_id=str(uuid4()), uid=msg.uid))
    else:
        ctx.logger.warning(f"Stamp failed ❌ response={payload_s}")

@consumer.on_message(UidResponse)
async def on_uid_resp(ctx: Context, sender: str, msg: UidResponse):
    payload = msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
    payload_s = json.dumps(payload, ensure_ascii=False)

    if msg.ok:
        ctx.logger.info(f"On-chain ✅ response={payload_s}")
    else:
        ctx.logger.warning(f"Status check failed ❌ response={payload_s}")

# -----------------------
# Helper (fire-and-forget)
# -----------------------
async def stamp_via_provider(ctx: Context, provider_address: str, hash_value: str) -> str:
    """Send a StampHashRequest and return the request_id (no waiting)."""
    request_id = str(uuid4())
    await ctx.send(provider_address, StampHashRequest(request_id=request_id, hash=hash_value))
    return request_id

# -----------------------
# Boot
# -----------------------
@consumer.on_event("startup")
async def go(ctx: Context):
    ctx.logger.info("BOOTING… waiting 10s before starting")
    await asyncio.sleep(10)

    rid = await stamp_via_provider(ctx, INTEGRITAS_AGENT_ADDRESS, HASH_TO_SEND)
    ctx.logger.info(f"Stamp request sent (request_id={rid}). Await async responses in on_stamp_resp/on_uid_resp.")

if __name__ == "__main__":
    consumer.run()
