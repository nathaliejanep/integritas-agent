# from fileinput import filename
# import os
import httpx
import traceback
import json
from uuid import uuid4
from datetime import datetime, timezone
# from sortedcontainers.sortedlist import identity
from uagents import Agent, Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, MetadataContent, ResourceContent,StartSessionContent, EndSessionContent, TextContent, chat_protocol_spec
)
from uagents_core.storage import ExternalStorage

from app.protocols.integritas_proto import (
    IntegritasProtocol,
    StampHashRequest, StampHashResponse, UidRequest, UidResponse,
    VerifyProofRequest, VerifyProofResponse, Error
)

from app.config.settings import AGENT_SEED, AGENT_PORT, AGENT_ENDPOINT, STORAGE_URL
from app.adapters.asi_client import ASIClient
from app.adapters.integritas_client import IntegritasClient
# from app.services import hashing_service
from app.services.intent_service import IntentService
from app.services.stamping_service import StampingService
from app.services.hashing_service import HashingService
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
hashing_service = HashingService()

# This is used to add metadata to the chat message for the agentverse storage
def create_metadata(metadata: dict[str, str]) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[MetadataContent(
            type="metadata",
            metadata=metadata,
        )],
    )


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info("Initiated chat")
    # ack
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id
    ))

    if any(isinstance(item, StartSessionContent) for item in msg.content):
        ctx.logger.info("StartSessionContent detected — skipping processing.")
        await ctx.send(sender, create_metadata({"attachments": "true"})) # Trigger metadata
        return

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent)).strip()
    if not text:
        return

    try:
        # First, detect uploaded files
        uploaded_files = []
        for item in msg.content:
            # Check if content is a file resource
            if isinstance(item, ResourceContent):
                try:
                    external_storage = ExternalStorage(
                        identity=ctx.agent.identity,
                        storage_url=STORAGE_URL,
                    )
                    data = external_storage.download(str(item.resource_id)) # Download the file from the agentverse storage
                    # print(f"data: {data}")
                    # Collect metadata for the file
                    uploaded_files.append({
                        "type": "resource", 
                        "mime_type": data["mime_type"], # file type
                        "contents": data["contents"], # file contents (bytes or string)
                        "filename": data.get("filename", "uploaded_file"),  # Extract filename
                    })
                    # print(f"uploaded_files: {uploaded_files}")
                    ctx.logger.info(f"Downloaded file: {data.get('filename', 'uploaded_file')}")

                except Exception as e:
                    ctx.logger.error(f"Failed to download file: {e}")
                    await _reply(ctx, sender, "Failed to download uploaded file.")
                    return

        # Enhance the text with file information for better intent detection
        enhanced_text = text
        if uploaded_files:
            filename = uploaded_files[0]["filename"]
            enhanced_text = f"{text} [File uploaded: {filename}]"

        intent = await intent_service.detect(enhanced_text)
        ctx.logger.info(f"Intent: {intent.kind}, payload: {intent.payload}")

        if intent.kind == "STAMP_HASH":
            # OLD CODE - COMMENTED OUT
            # hash_value = intent.payload.get("hash", "")
            # if len(hash_value) < 32:
            #     await _reply(ctx, sender, "The provided value doesn't look like a valid hash.")
            #     return

            # request_id = f"chat-{sender[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
            # uid = await stamping_service.stamp(hash_value, request_id)
            # if not uid:
            #     await _reply(ctx, sender, "❌ Failed to stamp hash. Please check the hash and try again.")
            #     return

            # await _reply(ctx, sender, f"✅ Hash stamped successfully!\n\n**UID:** {uid}\n\nChecking on‑chain confirmation...")

            # onchain = await stamping_service.wait_for_onchain(uid)
            # if onchain["onchain"]:
            #     proof = {
            #         "proof": onchain["proof"],
            #         "address": onchain["address"],
            #         "root": onchain["root"],
            #         "data": onchain["data"],
            #     }
            #     await _reply(ctx, sender, final_hash_confirmation(proof), end_session=True)
            # else:
            #     await _reply(ctx, sender, f"⏳ Status Update\n\n**UID:** {uid}\nStill waiting for blockchain confirmation.", end_session=True)
            # return

            # NEW CODE - Using reusable stamp_hash function
            hash_value = intent.payload.get("hash", "")
            
            # Create status callback function to get status updates
            async def status_callback(message):
                await _reply(ctx, sender, message)
            
            result = await stamping_service.stamp_hash(hash_value, sender, status_callback=status_callback)
            
            if not result["success"]:
                await _reply(ctx, sender, result["message"])
                return
            
            if result["onchain"]:
                await _reply(ctx, sender, final_hash_confirmation(result), end_session=True)
            else:
                await _reply(ctx, sender, result["message"], end_session=True)
            return

                # TODO: Improve this, by checking if not a proof file

        if intent.kind == "HASH_FILE":
            if uploaded_files:
                # Hash uploaded file using the reusable service method
                file_data = uploaded_files[0]
                hash_record = hashing_service.hash_uploaded_file(file_data)
                
                # Store the hash result in storage
                ctx.storage.set(f"hash_{hash_record['file_id']}", hash_record)
                
                await _reply(ctx, sender, f"✅ File hashed successfully!\n\n**Filename:** {hash_record['filename']}\n**Hash:** {hash_record['hash']}\n\nWould you like me to stamp this hash on the blockchain?")
            # else:
            #     # Check if file path was provided in intent
            #     file_path = intent.payload.get("file_path")
            #     if file_path:
            #         # Hash file from path
            #         ctx.logger.info(f"Attempting to hash file from path: {file_path}")
            #         hash_value = await hashing_service.hash_file(file_path)
            #         if hash_value:
            #             await _reply(ctx, sender, f"✅ File hashed successfully!\n\n**File:** {file_path}\n**Hash:** {hash_value}")
            #         else:
            #             await _reply(ctx, sender, f"❌ Could not hash file: {file_path}\n\nThis might be because:\n• The file doesn't exist at that location\n• The file path is not accessible from this agent\n• You don't have permission to read the file\n\n💡 **Tip:** For better reliability, try uploading the file directly instead of providing a file path. This works regardless of where the file is located on your system.\n\n📁 **Note:** If you want to use file paths, try using relative paths (like 'test_file.txt') instead of absolute paths.")
            #     else:
            #         # No file uploaded and no file path provided
            #         await _reply(ctx, sender, "I'd be happy to help you hash a file! Please upload a file or provide the file path so I can generate the hash for you.\n\n💡 **Recommended:** Upload the file directly for the most reliable experience.")
            return
        if intent.kind == "STAMP_FILE":
            if uploaded_files:
                # First hash the uploaded file
                file_data = uploaded_files[0]
                hash_record = hashing_service.hash_uploaded_file(file_data)
                
                # Store the hash result in storage
                ctx.storage.set(f"hash_{hash_record['file_id']}", hash_record)
                
                # Now stamp the hash using the reusable service method
                hash_value = hash_record['hash']
                
                # Create status callback function to get status updates
                async def status_callback(message):
                    await _reply(ctx, sender, message)
                
                result = await stamping_service.stamp_hash(hash_value, sender, status_callback=status_callback)
                
                if not result["success"]:
                    await _reply(ctx, sender, result["message"])
                    return
                
                if result["onchain"]:
                    await _reply(ctx, sender, final_hash_confirmation(result), end_session=True)
                else:
                    await _reply(ctx, sender, result["message"], end_session=True)
            else:
                await _reply(ctx, sender, "I'd be happy to stamp a file for you! Please upload a file so I can hash it and then stamp the hash on the blockchain.")
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

        if intent.kind == "VERIFY_PROOF_FILE":
            # print(f"Step 3: Handling VERIFY_PROOF_FILE intent")
            # print(f"Step 3: Uploaded files count: {len(uploaded_files)}")
            
            if not uploaded_files:
                await _reply(ctx, sender, "❌ No file uploaded. Please upload a proof file to verify.")
                return
            
            # Check if the uploaded file is a valid proof file
            file_data = uploaded_files[0]
            # print(f"Step 3: File data keys: {list(file_data.keys())}")
            # print(f"Step 3: File mime_type: {file_data.get('mime_type')}")
            # print(f"Step 3: File filename: {file_data.get('filename')}")
            
            if not verification_service.is_proof_file(file_data):
                await _reply(ctx, sender, "❌ The uploaded file is not a valid proof file. Please ensure it's a JSON file with the required structure containing address, data, proof, and root properties.")
                return
            
            # print(f"Step 3: Proof file validation successful, proceeding to verification")
            
            # Parse the proof file to extract verification data
            try:
                first_proof = verification_service.parse_proof_file(file_data)
                
                # print(f"Step 3: Extracted proof data: {first_proof}")
                
                # Use the same verification logic as VERIFY_PROOF
                # print(f"Step 4: Using same verification logic as existing verify function")
                request_id = f"chat-{sender[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
                # print(f"first_proof: {first_proof['proof']}")
                verification = await verification_service.verify(
                    proof=first_proof["proof"], 
                    root=first_proof["root"], 
                    address=first_proof["address"], 
                    data=first_proof["data"], 
                    request_id=request_id
                )
                
                if not verification:
                    await _reply(ctx, sender, "❌ Failed to verify proof from file. Please check your proof file and try again.")
                    return

                # Ask ASI to produce a human explanation (same as VERIFY_PROOF)
                # print(f"Step 4: Using same response format as existing verify function")
                reason = await asi.explain_verification(docs, json.dumps(verification))
                await _reply(ctx, sender, verification_report(verification, reason), end_session=True)
                return
                
            except Exception as e:
                print(f"❌ Error processing proof file: {e}")
                await _reply(ctx, sender, f"❌ Error processing proof file: {str(e)}")
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
