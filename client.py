# Client Agent - This agent sends hash data to the integritas agent
# It acts as a client that sends hash verification requests

from uagents import Agent, Context, Field, Model, Protocol
from pydantic import BaseModel, Field
 
# Create a client agent with a unique name, seed, and endpoint
# Note: Using port 8001 to avoid conflicts with the AI agent (port 8000)
agent = Agent(name="test client agent",
              seed="your seed value alt",
              port=8001,
              endpoint=["http://127.0.0.1:8001/submit"]
              )
 
# The hash that this client will send to the integritas agent
HASH_TO_SEND = "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"
 
 
# Define the data model for hash data sent to the integritas agent
class HashRequest(BaseModel):
    hash: str = Field(
        description="The hash data that needs to be processed by the integritas agent."
    )
 
 
# Define the data model for responses received from the integritas agent
class StampResponse(BaseModel):
    message: str = Field(
        description="The response message from integritas agent"
    )
    proof: str = Field(
        description="The proof returned from Integritas API if successful, empty string if failed",
    )
    root: str = Field(
        description="The root returned from Integritas API if successful, empty string if failed",
    )
    address: str = Field(
        description="The address returned from Integritas API if successful, empty string if failed",
    )
    data: str = Field(
        description="The data returned from Integritas API if successful, empty string if failed",
    )
    success: bool = Field(
        description="Whether the hash was successfully stamped",
        default=False
    )
 
class Start(BaseModel):
    message: str = Field(
        description="The message to send to the integritas agent"
    )
 
# 1. Event handler that sends hash when client agent starts up
@agent.on_event("startup") # Real scenario would be on message from something?
async def send_hash(ctx: Context):
    # Log what hash we're about to send
    ctx.logger.info(
        f"Sending hash to integritas agent: {HASH_TO_SEND}"
    )
    
    # if booking made, send hash to integritas agent

    # Send the hash to the integritas agent
    # The address below is the integritas agent's unique address (from integritas_agent.py startup log)
    await ctx.send(
        'agent1qdpzrc02a8lnlzaahtdyy3wnaux64pqa22vykp59tx67jx2mmy3dzf249jk', HashRequest(hash=HASH_TO_SEND)
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