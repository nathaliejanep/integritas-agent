# Client Agent - This agent sends hash data to the integritas agent
# It acts as a client that sends hash verification requests

from uagents import Agent, Context, Model

 
# Create a client agent with a unique name, seed, and endpoint
# Note: Using port 8001 to avoid conflicts with the AI agent (port 8000)
agent = Agent(name="test client agent",
              seed="your skt78keed value a78,t78klt",
              port=8001,
              endpoint=["http://127.0.0.1:8001/submit"]
              )
 
# The hash that this client will send to the integritas agent
HASH_TO_SEND = "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"

class Message(Model):
    message: str 
 
class HashRequest(Model):
    hash: str
 
class StampResponse(Model):
    message: str
    proof: str
    root: str
    address: str
    data: str
    success: bool

class VerifyRequest(Model):
    proof: str
    root: str
    address: str 
    data: str

class VerifyResponse(Model):
    api_version: int
    request_id: str
    status: str
    status_code: int
    message: str
    timestamp: str
    data: dict

class Start(Model):
    message: str



# 1. Event handler that sends hash when client agent starts up
@agent.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):

    ctx.logger.info(f"Received message from {sender}: {msg.message}")
    
    if msg.message == "start":
    
    # if booking made, send hash to integritas agent

    # Send the hash to the integritas agent
    # The address below is the integritas agent's unique address (from integritas_agent.py startup log)
        await ctx.send(
            'agent1qtzl2h4cggmrqpnxtlvzw23wnmjwk874af4cr30rqzp63kf4ry36krgwf5l', HashRequest(hash=HASH_TO_SEND)
        )
    
 
# 3. Message handler that processes stamp response from the integritas agent and sends response back to verify_client if success
@agent.on_message(model=StampResponse)
async def handle_response(ctx: Context, sender: str, data: StampResponse):
    # Log the response received from the integritas agent
    ctx.logger.info(f"Got response from integritas agent: {data.message}")
    
    if data.success:
        ctx.logger.info(f"Proof: {data.proof} Root: {data.root} Address: {data.address} Data: {data.data}")
        await ctx.send(
            'agent1qwrv654kc3axm53mp2yc0e22kxafhju8htk2u5sltwez3088tkdrkhxu0er', StampResponse(message=data.message, proof=data.proof, root=data.root, address=data.address, data=data.data, success=data.success)
        )
    else:
        ctx.logger.error("Hash stamping failed!")


# @agent.on_message(model=Start)
# async def send_hash(ctx: Context):
#     # Log what hash we're about to send
#     ctx.logger.info(
#         f"Sending hash to integritas agent: {HASH_TO_SEND}"
#     )
    
#     # if booking made, send hash to integritas agent

#     # Send the hash to the integritas agent
#     # The address below is the integritas agent's unique address (from integritas_agent.py startup log)
#     await ctx.send(
#         'agent1qdpzrc02a8lnlzaahtdyy3wnaux64pqa22vykp59tx67jx2mmy3dzf249jk', HashRequest(hash=HASH_TO_SEND)
#     )

# Start the client agent - this will send the hash and wait for the response
agent.run()