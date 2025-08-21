import os
import httpx
import traceback
import json
from uuid import uuid4
from datetime import datetime, timezone
from uagents import Agent, Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, StartSessionContent, EndSessionContent, TextContent, chat_protocol_spec
)

from app.protocols.integritas_proto import (
    IntegritasProtocol,
    StampHashRequest, StampHashResponse, UidRequest, UidResponse,
    VerifyProofRequest, VerifyProofResponse, Error
)

from app.config.settings import AGENT_SEED, AGENT_PORT, AGENT_ENDPOINT
from app.adapters.asi_client import ASIClient
from app.adapters.integritas_client import IntegritasClient
from app.services.intent_service import IntentService
from app.services.stamping_service import StampingService
from app.services.verification_service import VerificationService
from app.formatters.chat_presenters import final_hash_confirmation, verification_report
from app.integritas_docs import docs  # keep your docs string here or move under /config

# --- Agent + Protocols
agent = Agent(
    name="integritas_agent",
    port=AGENT_PORT,
    seed=AGENT_SEED,
    endpoint=[AGENT_ENDPOINT],
    mailbox=True,
    readme_path="README.md",
)

protocol = Protocol(spec=chat_protocol_spec)

# --- DI singletons (kept simple)
asi = ASIClient()
integ = IntegritasClient()
intent_service = IntentService(asi)
stamping_service = StampingService(integ)
verification_service = VerificationService(integ)

@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info("Initiated chat")
    # ack
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id
    ))

    if any(isinstance(item, StartSessionContent) for item in msg.content):
        ctx.logger.info("StartSessionContent detected — skipping processing.")
        return

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent)).strip()
    if not text:
        return

    try:
        intent = await intent_service.detect(text)
        ctx.logger.info(f"Intent: {intent.kind}, payload: {intent.payload}")

        if intent.kind == "STAMP_HASH":
            hash_value = intent.payload.get("hash", "")
            if len(hash_value) < 32:
                await _reply(ctx, sender, "The provided value doesn't look like a valid hash.")
                return

            request_id = f"chat-{sender[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
            uid = await stamping_service.stamp(hash_value, request_id)
            if not uid:
                await _reply(ctx, sender, "❌ Failed to stamp hash. Please check the hash and try again.")
                return

            await _reply(ctx, sender, f"✅ Hash stamped successfully!\n\n**UID:** {uid}\n\nChecking on‑chain confirmation...")

            onchain = await stamping_service.wait_for_onchain(uid)
            if onchain["onchain"]:
                proof = {
                    "proof": onchain["proof"],
                    "address": onchain["address"],
                    "root": onchain["root"],
                    "data": onchain["data"],
                }
                await _reply(ctx, sender, final_hash_confirmation(proof), end_session=True)
            else:
                await _reply(ctx, sender, f"⏳ Status Update\n\n**UID:** {uid}\nStill waiting for blockchain confirmation.", end_session=True)
            return

        if intent.kind == "VERIFY_PROOF":
            pd = intent.payload
            # Basic validation
            missing = [k for k in ("data", "root", "address", "proof") if k not in pd]
            if missing:
                await _reply(ctx, sender, f"Missing keys in JSON: {', '.join(missing)}.")
                return

            request_id = f"chat-{sender[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
            verification = await verification_service.verify(
                proof=pd["proof"], root=pd["root"], address=pd["address"], data=pd["data"], request_id=request_id
            )
            if not verification:
                await _reply(ctx, sender, "❌ Failed to verify proof. Please check your data and try again.")
                return

            # Ask ASI to produce a human explanation
            reason = await asi.explain_verification(docs, json.dumps(verification))
            await _reply(ctx, sender, verification_report(verification, reason), end_session=True)
            return

        # GENERAL: forward ASI content as-is (no links mandated by your system prompt)
        await _reply(ctx, sender, intent.raw_response)

    except Exception as e:
        ctx.logger.exception("Handler error")
        await _reply(ctx, sender, "I’m sorry—something went wrong while processing your request.")

# async def _reply(ctx: Context, to: str, text: str, end_session: bool = False):
#     contents = [TextContent(type="text", text=text)]
#     await ctx.send(to, ChatMessage(
#         timestamp=datetime.now(timezone.utc),
#         msg_id=uuid4(),
#         content=contents
#     ))

async def _reply(ctx: Context, to: str, text: str, end_session: bool = False):
    contents = [TextContent(type="text", text=text)]
    if end_session:
        contents.append(EndSessionContent(type="end-session"))
    await ctx.send(
        to,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=contents,
        ),
    )

# 2) Structured protocol (agent↔agent RPC)
@IntegritasProtocol.on_message(StampHashRequest)
async def rpc_stamp(ctx: Context, sender: str, msg: StampHashRequest):
    ctx.logger.info("Stamp requested")
    try:
        if not msg.hash or len(msg.hash) < 32:
            await ctx.send(sender, StampHashResponse(
                request_id=msg.request_id, ok=False,
                error=Error(code="BAD_REQUEST", message="Invalid hash")
            ))
            return

        uid = await stamping_service.stamp(msg.hash, request_id=f"rpc-{msg.request_id}")
        if not uid:
            await ctx.send(sender, StampHashResponse(
                request_id=msg.request_id, ok=False,
                error=Error(code="INTERNAL", message="Stamping failed")
            ))
            return

        await ctx.send(sender, StampHashResponse(
            request_id=msg.request_id, ok=True, uid=uid
        ))
    except Exception as e:
        ctx.logger.exception("rpc_stamp error")
        await ctx.send(sender, StampHashResponse(
            request_id=msg.request_id, ok=False,
            error=Error(code="INTERNAL", message=str(e))
        ))

@IntegritasProtocol.on_message(UidRequest)
async def rpc_status(ctx: Context, sender: str, msg: UidRequest):
    ctx.logger.info("Uid status Requested")
    try:
        if not msg.uid or len(msg.uid) < 20:
            await ctx.send(sender, UidResponse(
                request_id=msg.request_id, ok=False,
                error=Error(code="BAD_REQUEST", message="Invalid uid")
            ))
            return

        proof = await stamping_service.wait_for_onchain(msg.uid)
        if not proof:
            await ctx.send(sender, UidResponse(
                request_id=msg.request_id, ok=False,
                error=Error(code="INTERNAL", message="Status check failed")
            ))
            return

        await ctx.send(sender, UidResponse(
            request_id=msg.request_id, ok=True, proof=proof["proof"], root=proof["root"], address=proof["address"], data=proof["data"] 
        ))
    except Exception as e:
        ctx.logger.exception("rpc_status error")
        await ctx.send(sender, UidResponse(
            request_id=msg.request_id, ok=False,
            error=Error(code="INTERNAL", message=str(e))
        ))

@IntegritasProtocol.on_message(VerifyProofRequest)
async def rpc_verify(ctx: Context, sender: str, msg: VerifyProofRequest):
    ctx.logger.info("Verify Proof Requested")
    # try:
    #     for key in ("proof","root","address","data"):
    #         if not getattr(msg, key, None):
    #             await ctx.send(sender, VerifyProofResponse(
    #                 request_id=msg.request_id, ok=False,
    #                 error=Error(code="BAD_REQUEST", message=f"Missing '{key}'")
    #             ))
    #             return

    #     report = await verification_service.verify(
    #         proof=msg.proof, root=msg.root, address=msg.address, data=msg.data,
    #         request_id=f"rpc-{msg.request_id}"
    #     )
    #     if not report:
    #         await ctx.send(sender, VerifyProofResponse(
    #             request_id=msg.request_id, ok=False,
    #             error=Error(code="INTERNAL", message="Verify failed")
    #         ))
    #         return

    #     await ctx.send(sender, VerifyProofResponse(
    #         request_id=msg.request_id, ok=True, report=report
    #     ))
    # except Exception as e:
    #     ctx.logger.exception("rpc_verify error")
    #     await ctx.send(sender, VerifyProofResponse(
    #         request_id=msg.request_id, ok=False,
    #         error=Error(code="INTERNAL", message=str(e))
    #     ))
    try:
        # 1) basic shape check
        for key in ("proof","root","address","data"):
            if not getattr(msg, key, None):
                await ctx.send(sender, VerifyProofResponse(
                    request_id=msg.request_id, ok=False,
                    error=Error(code="BAD_REQUEST", message=f"Missing '{key}'")
                ))
                return

        # 2) call upstream
        report = await verification_service.verify(
            proof=msg.proof, root=msg.root, address=msg.address, data=msg.data,
            request_id=f"rpc-{msg.request_id}"
        )
        if not report:
            await ctx.send(sender, VerifyProofResponse(
                request_id=msg.request_id, ok=False,
                error=Error(code="INTERNAL", message="Verify failed (empty report)")
            ))
            return

        await ctx.send(sender, VerifyProofResponse(
            request_id=msg.request_id, ok=True, report=report
        ))

    except httpx.TimeoutException as e:
        ctx.logger.exception("rpc_verify timeout")
        await ctx.send(sender, VerifyProofResponse(
            request_id=msg.request_id, ok=False,
            error=Error(code="TIMEOUT", message="Upstream verify timed out")
        ))

    except httpx.HTTPStatusError as e:
        # Make sure your integritas client calls .raise_for_status() so we land here
        status = e.response.status_code
        body_preview = (e.response.text or "")[:300]
        code = "BAD_REQUEST" if 400 <= status < 500 else "INTERNAL"
        ctx.logger.exception("rpc_verify HTTPStatusError")
        await ctx.send(sender, VerifyProofResponse(
            request_id=msg.request_id, ok=False,
            error=Error(code=code, message=f"HTTP {status}: {body_preview}")
        ))

    except httpx.HTTPError as e:
        # DNS/Connect/Protocol errors, etc.
        ctx.logger.exception("rpc_verify HTTPError")
        await ctx.send(sender, VerifyProofResponse(
            request_id=msg.request_id, ok=False,
            error=Error(code="INTERNAL", message=f"{e.__class__.__name__}: {e!s}")
        ))

    except Exception as e:
        # Anything else; include type + short traceback for your logs
        tb = traceback.format_exc(limit=5)
        ctx.logger.error(f"rpc_verify error: {e!r}\n{tb}")
        await ctx.send(sender, VerifyProofResponse(
            request_id=msg.request_id, ok=False,
            error=Error(code="INTERNAL", message=f"{e.__class__.__name__}")
        ))

@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )

agent.include(protocol, publish_manifest=True)
agent.include(IntegritasProtocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
