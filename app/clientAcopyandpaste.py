import asyncio
from uagents import Agent, Context, Model, Protocol
from typing import Literal, Optional, Dict, Any
from uuid import uuid4

# ----- Common -----
class Error(Model):
    code: Literal["BAD_REQUEST","UNAUTHORIZED","NOT_FOUND","TIMEOUT","INTERNAL"]
    message: str

class BaseRequest(Model):
    request_id: str
    # (optional) security / auth metadata
    # nonce: Optional[str]
    # signature: Optional[str]
    # timestamp: Optional[str]

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

INTEGRITAS_AGENT_ADDRESS = "agent1q0wh8zvtn90eankda62qu3yj56h0fp2gpsxu0kevpywaxu480r9ujsdyt25"

# -----------------------
# Config
# -----------------------
consumer = Agent(name="integritas_consumer_a", seed="cons-seed-asdadf3wff3", port=8001,
                 endpoint=["http://127.0.0.1:8001/submit"])


HASH_TO_SEND = "4dd7cac4f6d591d0283d5a6c18ac1b8cb9294de94253f59a004fd6b721cfe7cf"


# -----------------------
# Pending map
# -----------------------
# Pattern A: We resolve the future on the stamp response and return it to the caller.
# The on-chain status check is *not* tied to that same future (fire-and-forget).
pending_stamp: Dict[str, asyncio.Future] = {}


# -----------------------
# Handlers
# -----------------------
@consumer.on_message(StampHashResponse)
async def on_stamp_resp(ctx: Context, sender: str, msg: StampHashResponse):
    """Complete the stamp future immediately. Then *optionally* trigger a fire-and-forget status check."""
    fut = pending_stamp.pop(msg.request_id, None)
    if fut and not fut.done():
        fut.set_result(msg)

    # Fire-and-forget status check (only if stamping succeeded and we have a UID)
    if msg.ok and msg.uid:
        ctx.logger.info("Stamp succeeded; waiting 10s before sending status request…")
        await asyncio.sleep(10)
        await ctx.send(sender, UidRequest(request_id=str(uuid4()), uid=msg.uid))
    else:
        ctx.logger.warning(f"Stamp failed or missing UID: {msg.error}")


@consumer.on_message(UidResponse)
async def on_uid_resp(ctx: Context, sender: str, msg: UidResponse):
    """We’re using Pattern A, so just log whatever comes back from status."""
    if msg.ok:
        ctx.logger.info(f"""*Status result*
    proof:
    {msg.proof}
    root:
    {msg.root}
    data:
    {msg.data}
    address:
    {msg.address}
    """)
    else:
        ctx.logger.warning(f"Status check failed: {msg.error}")

# -----------------------
# Helper
# -----------------------
async def stamp_via_provider(ctx: Context, provider_address: str, hash_value: str, timeout=30):
    """Send a StampHashRequest and resolve when the stamp response arrives.
    (Does NOT wait for on-chain status; that is fire-and-forget in the handler.)
    """
    request_id = str(uuid4())
    fut = asyncio.get_event_loop().create_future()
    pending_stamp[request_id] = fut

    await ctx.send(provider_address, StampHashRequest(request_id=request_id, hash=hash_value))

    try:
        result = await asyncio.wait_for(fut, timeout=timeout)
        return result  # StampHashResponse
    except asyncio.TimeoutError:
        pending_stamp.pop(request_id, None)
        return StampHashResponse(
            request_id=request_id,
            ok=False,
            error=Error(code="TIMEOUT", message="No stamp response within timeout"),
        )
    
# -----------------------
# Boot
# -----------------------
@consumer.on_event("startup")
async def go(ctx: Context):
    ctx.logger.info("BOOTING... waiting 10s before starting")
    await asyncio.sleep(10)   # ⏳ wait 10 seconds

    stamp = await stamp_via_provider(ctx, INTEGRITAS_AGENT_ADDRESS, HASH_TO_SEND, timeout=60)
    if stamp.ok:
        ctx.logger.info(f"Stamped ✅ uid={stamp.uid}")
    else:
        ctx.logger.warning(f"Stamp failed: {stamp.error}")

if __name__ == "__main__":
    consumer.run()
