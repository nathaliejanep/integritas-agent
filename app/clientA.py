# # Client Agent - This agent sends hash data to the integritas agent
# # It acts as a client that sends hash verification requests

# from uagents import Agent, Context, Model

 
# # Create a client agent with a unique name, seed, and endpoint
# # Note: Using port 8001 to avoid conflicts with the AI agent (port 8000)
# agent = Agent(name="test client agent",
#               seed="your skt78keed value a78,t78klt",
#               port=8001,
#               endpoint=["http://127.0.0.1:8001/submit"]
#               )
 
# # The hash that this client will send to the integritas agent
# HASH_TO_SEND = "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"

# class Message(Model):
#     message: str 
 
# class HashRequest(Model):
#     hash: str
 
# class StampResponse(Model):
#     message: str
#     proof: str
#     root: str
#     address: str
#     data: str
#     success: bool

# class VerifyRequest(Model):
#     proof: str
#     root: str
#     address: str 
#     data: str

# class VerifyResponse(Model):
#     api_version: int
#     request_id: str
#     status: str
#     status_code: int
#     message: str
#     timestamp: str
#     data: dict

# class Start(Model):
#     message: str



# # 1. Event handler that sends hash when client agent starts up
# @agent.on_message(model=Message)
# async def message_handler(ctx: Context, sender: str, msg: Message):

#     ctx.logger.info(f"Received message from {sender}: {msg.message}")
    
#     if msg.message == "start":
    
#     # if booking made, send hash to integritas agent

#     # Send the hash to the integritas agent
#     # The address below is the integritas agent's unique address (from integritas_agent.py startup log)
#         await ctx.send(
#             'agent1qwtpec3kpv9eqep5cztyscngfwz6azn9dlsy9urgjmkju3xesnumync455x', HashRequest(hash=HASH_TO_SEND)
#         )
    
 
# # 3. Message handler that processes stamp response from the integritas agent and sends response back to verify_client if success
# @agent.on_message(model=StampResponse)
# async def handle_response(ctx: Context, sender: str, data: StampResponse):
#     # Log the response received from the integritas agent
#     ctx.logger.info(f"Got response from integritas agent: {data.message}")
    
#     if data.success:
#         ctx.logger.info(f"Proof: {data.proof} Root: {data.root} Address: {data.address} Data: {data.data}")
#         await ctx.send(
#             'agent1qwrv654kc3axm53mp2yc0e22kxafhju8htk2u5sltwez3088tkdrkhxu0er', StampResponse(message=data.message, proof=data.proof, root=data.root, address=data.address, data=data.data, success=data.success)
#         )
#     else:
#         ctx.logger.error("Hash stamping failed!")


# # @agent.on_message(model=Start)
# # async def send_hash(ctx: Context):
# #     # Log what hash we're about to send
# #     ctx.logger.info(
# #         f"Sending hash to integritas agent: {HASH_TO_SEND}"
# #     )
    
# #     # if booking made, send hash to integritas agent

# #     # Send the hash to the integritas agent
# #     # The address below is the integritas agent's unique address (from integritas_agent.py startup log)
# #     await ctx.send(
# #         'agent1qdpzrc02a8lnlzaahtdyy3wnaux64pqa22vykp59tx67jx2mmy3dzf249jk', HashRequest(hash=HASH_TO_SEND)
# #     )

# # Start the client agent - this will send the hash and wait for the response
# agent.run()

# agents/consumer.py (excerpt)
import asyncio
from uagents import Agent, Context
from app.protocols.integritas_proto import (
    IntegritasProtocol,
    StampHashRequest, StampHashResponse,
    VerifyProofRequest, VerifyProofResponse
)
from uuid import uuid4

consumer = Agent(name="integritas_consumer", seed="cons-seed", port=8002,
                 endpoint=["http://127.0.0.1:8002/submit"])

# Simple in-memory pending map
pending: dict[str, asyncio.Future] = {}

@IntegritasProtocol.on_message(StampHashResponse)
async def on_stamp_resp(ctx: Context, sender: str, msg: StampHashResponse):
    fut = pending.pop(msg.request_id, None)
    if fut and not fut.done():
        fut.set_result(msg)

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
    provider_address = "agent1qwtpec3kpv9eqep5cztyscngfwz6azn9dlsy9urgjmkju3xesnumync455x"  # paste the provider’s on-chain/known address
    resp = await stamp_via_provider(ctx, provider_address, "aabbcc...hash...")
    if resp.ok:
        ctx.logger.info(f"Stamped! uid={resp.uid}")
    else:
        ctx.logger.warning(f"Stamp failed: {resp.error}")

if __name__ == "__main__":
    consumer.run()