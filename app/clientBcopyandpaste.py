import asyncio
import json
from uagents import Agent, Context, Model
from typing import Literal, Optional, Dict, Any
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

# ----- Verify Proof -----
class VerifyProofRequest(BaseRequest):
    proof: str
    root: str
    address: str
    data: str

class VerifyProofResponse(BaseResponse):
    report: Optional[Dict[str, Any]] = None

INTEGRITAS_AGENT_ADDRESS = "agent1q2svq8ukmatt8edfpp4heckcmxpk7gchelecf2v98pf723w932dsst7059g"

# -----------------------
# Config
# -----------------------

consumer = Agent()

# ENTER THE PROOF DATA YOU WISH TO VERIFY HERE
PROOF_TO_VERIFY = {
    "proof": "",
    "root": "",
    "data": "",
    "address": "",
}

# -----------------------
# Handlers
# -----------------------
@consumer.on_message(VerifyProofResponse)
async def on_verify_resp(ctx: Context, sender: str, msg: VerifyProofResponse):
    payload = msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
    payload_s = json.dumps(payload, ensure_ascii=False)

    if msg.ok:
        ctx.logger.info(f"Verification success ✅ response={payload_s}")
    else:
        ctx.logger.warning(f"Verification failed ❌ response={payload_s}")


# -----------------------
# Helper
# -----------------------
async def verify_via_provider(ctx: Context, provider_address: str, *, proof) -> str:
    """Fire-and-forget send. Returns the request_id for logging."""
    request_id = str(uuid4())
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
    return request_id

# -----------------------
# Boot
# -----------------------
@consumer.on_event("startup")
async def go(ctx: Context):
    ctx.logger.info("BOOTING… waiting 10s before starting")
    await asyncio.sleep(10)

    rid = await verify_via_provider(ctx, INTEGRITAS_AGENT_ADDRESS, proof=PROOF_TO_VERIFY)
    ctx.logger.info(f"Verify request sent (request_id={rid}). Await the async response in on_verify_resp.")

if __name__ == "__main__":
    consumer.run()