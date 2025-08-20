

import asyncio
from uagents import Agent, Context
from app.protocols.integritas_proto import (
    IntegritasProtocol,
    StampHashRequest, StampHashResponse,
    VerifyProofRequest, VerifyProofResponse
)
from uuid import uuid4

consumer = Agent(name="integritas_consumer_b", seed="cons-seed-b45w5ww645", port=8002,
                 endpoint=["http://127.0.0.1:8002/submit"])

# The PROOF received by clientB from the integritas agent
PROOF_TO_VERIFY = ""

# Simple in-memory pending map
pending: dict[str, asyncio.Future] = {}

@IntegritasProtocol.on_message(VerifyProofResponse)
async def on_verify_resp(ctx: Context, sender: str, msg: VerifyProofResponse):
    fut = pending.pop(msg.request_id, None)
    if fut and not fut.done():
        fut.set_result(msg)

consumer.include(IntegritasProtocol, publish_manifest=True)

# ---- high-level helpers the consumer can call from anywhere ----
async def stamp_via_provider(ctx: Context, provider_address: str, hash_value: str, timeout=30):
    request_id = str(uuid4())
    fut = asyncio.get_event_loop().create_future()
    pending[request_id] = fut

    await ctx.send(provider_address, StampHashRequest(request_id=request_id, hash=hash_value))
    try:
        return await asyncio.wait_for(fut, timeout=timeout)
    except asyncio.TimeoutError:
        pending.pop(request_id, None)
        return StampHashResponse(request_id=request_id, ok=False, error={"code":"TIMEOUT","message":"No response"})

async def verify_via_provider(ctx: Context, provider_address: str, *, proof, root, address, data, timeout=30):
    request_id = str(uuid4())
    fut = asyncio.get_event_loop().create_future()
    pending[request_id] = fut

    await ctx.send(provider_address, VerifyProofRequest(
        request_id=request_id, proof=proof, root=root, address=address, data=data
    ))
    try:
        return await asyncio.wait_for(fut, timeout=timeout)
    except asyncio.TimeoutError:
        pending.pop(request_id, None)
        return VerifyProofResponse(request_id=request_id, ok=False, error={"code":"TIMEOUT","message":"No response"})
    
@consumer.on_event("startup")
async def go(ctx: Context):
    ctx.logger.info(f"BOOTING")
    provider_address = "agent1q0wh8zvtn90eankda62qu3yj56h0fp2gpsxu0kevpywaxu480r9ujsdyt25"  # paste the provider’s on-chain/known address
    resp = await stamp_via_provider(ctx, provider_address, HASH_TO_SEND)
    if resp.ok:
        ctx.logger.info(f"Stamped! uid={resp.uid}")
    else:
        ctx.logger.warning(f"Stamp failed: {resp.error}")

if __name__ == "__main__":
    consumer.run()