import os
import json
from uuid import uuid4
from datetime import datetime, timezone
from uagents import Agent, Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, StartSessionContent, EndSessionContent, TextContent, chat_protocol_spec
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
    name="asi_integritas_agent",
    seed=AGENT_SEED,
    port=AGENT_PORT,
    endpoint=[AGENT_ENDPOINT],
)

protocol = Protocol(spec=chat_protocol_spec)

# --- DI singletons (kept simple)
asi = ASIClient()
integ = IntegritasClient()
intent_service = IntentService(asi)
stamping_service = StampingService(integ)
verification_service = VerificationService(integ)

class HashRequest(Model):
    hash: str

@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
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

async def _reply(ctx: Context, to: str, text: str, end_session: bool = False):
    contents = [TextContent(type="text", text=text)]
    await ctx.send(to, ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=contents
    ))

print("Spec:", chat_protocol_spec.name, chat_protocol_spec.version)
agent.include(protocol, publish_manifest=False)

if __name__ == "__main__":
    agent.run()
