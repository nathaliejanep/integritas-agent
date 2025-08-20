import asyncio
import json
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

# ----- Verify Proof -----
class VerifyProofRequest(BaseRequest):
    proof: str
    root: str
    address: str
    data: str

class VerifyProofResponse(BaseResponse):
    report: Optional[Dict[str, Any]] = None  # raw API result (or normalized)

# -----------------------
# Config
# -----------------------

consumer = Agent(name="integritas_consumer_b", seed="cons-seed-b45w5ww645", port=8002,
                 endpoint=["http://127.0.0.1:8002/submit"])

INTEGRITAS_AGENT_ADDRESS = "agent1q0wh8zvtn90eankda62qu3yj56h0fp2gpsxu0kevpywaxu480r9ujsdyt25"

PROOF_TO_VERIFY = {
    "proof": "0x000100000100",
    "root": "0xDAD7F057C70DE3BC4756AB871836CB0BF1128EDB63025AD2587167EE683564D3",
    "data": "0x4dd7cac4f6d591d0283d5a6c18ac1b8cb9294de94253f59a004fd6b721cfe7cf",
    "address": "0xFFEEDD",
}

# -----------------------
# Pending map
# -----------------------
# Track pending verification requests (Pattern A: only for verify responses)
pending_verify: Dict[str, asyncio.Future] = {}

# -----------------------
# Handlers
# -----------------------
@consumer.on_message(VerifyProofResponse)
async def on_verify_resp(ctx: Context, sender: str, msg: VerifyProofResponse):
    fut = pending_verify.pop(msg.request_id, None)
    if fut and not fut.done():
        fut.set_result(msg)

# -----------------------
# Helper
# -----------------------
async def verify_via_provider(ctx: Context, provider_address: str, *, proof, timeout=30):
    # request_id = str(uuid4())
    # fut = asyncio.get_event_loop().create_future()
    # pending_verify[request_id] = fut

    # await ctx.send(provider_address, VerifyProofRequest(
    #     request_id=request_id, proof=proof["proof"], root=proof["root"], address=proof["address"], data=proof["data"]
    # ))
    # try:
    #     return await asyncio.wait_for(fut, timeout=timeout)
    # except asyncio.TimeoutError:
    #     pending_verify.pop(request_id, None)
    #     return VerifyProofResponse(request_id=request_id, ok=False, error={"code":"TIMEOUT","message":"No response"})
    """Send a VerifyProofRequest and resolve when the verify response arrives."""
    request_id = str(uuid4())
    fut = asyncio.get_running_loop().create_future()
    pending_verify[request_id] = fut

    await ctx.send(
        provider_address,
        VerifyProofRequest(
            request_id=request_id,
            proof=proof["proof"],
            root=proof["root"],
            address=proof["address"],
            data=proof["data"],
        ),
    )

    try:
        return await asyncio.wait_for(fut, timeout=timeout)
    except asyncio.TimeoutError:
        pending_verify.pop(request_id, None)
        return VerifyProofResponse(
            request_id=request_id,
            ok=False,
            error=Error(code="TIMEOUT", message="No verify response within timeout"),
        )

# -----------------------
# Boot
# -----------------------
@consumer.on_event("startup")
async def go(ctx: Context):
    # ctx.logger.info("BOOTING... waiting 10s before starting")
    # await asyncio.sleep(10)   # ⏳ wait 10 seconds

    # resp = await verify_via_provider(ctx, INTEGRITAS_AGENT_ADDRESS, proof=PROOF_TO_VERIFY)
    # if resp.ok:
    #     ctx.logger.info(f"Verification success! uid={resp.data}")
    # else:
    #     ctx.logger.warning(f"Verifying failed: {resp.error}")
    ctx.logger.info("BOOTING… waiting 10s before starting")
    await asyncio.sleep(10)

    resp = await verify_via_provider(ctx, INTEGRITAS_AGENT_ADDRESS, proof=PROOF_TO_VERIFY, timeout=60)
    if resp.ok:
        payload = resp.model_dump() if hasattr(resp, "model_dump") else resp.dict()
        ctx.logger.info(
            "Verification success ✅ full VerifyProofResponse:\n%s",
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        )
    else:
        err = getattr(resp.error, "message", "") if resp.error else ""
        code = getattr(resp.error, "code", "UNKNOWN")
        ctx.logger.warning(f"Verification failed ❌ [{code}]: {err}")

if __name__ == "__main__":
    consumer.run()