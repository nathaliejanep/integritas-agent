# Client Agent - This agent sends hash data to the integritas agent
# It acts as a client that sends hash verification requests

from uagents import Agent, Context, Field, Model, Protocol
from pydantic import BaseModel, Field
 
# Create a client agent with a unique name, seed, and endpoint
# Note: Using port 8002 to avoid conflicts with the integritas agent (port 8000)
agent = Agent(name="verify client agent",
              seed="your seed value client verify",
              port=8002,
              endpoint=["http://127.0.0.1:8002/submit"]
              )
 
# Define the data model for sending hash requests to the integritas agent
class HashRequest(BaseModel):
    hash: str = Field(
        description="The hash data that needs to be processed by the integritas agent."
    )

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

class VerifyResponse(BaseModel):
    response: str = Field(
        description="The response from the integritas agent"
    )

@agent.on_event("startup")
async def print_address(ctx: Context):
    # Log the agent's unique address so other agents know where to send messages
    ctx.logger.info(agent.address)

@agent.on_message(model=StampResponse)
async def handle_response(ctx: Context, sender: str, data: StampResponse):
    if data.success:
        ctx.logger.info(f"Proof: {data.proof} Root: {data.root} Address: {data.address} Data: {data.data}")
        await ctx.send(
            'agent1qdpzrc02a8lnlzaahtdyy3wnaux64pqa22vykp59tx67jx2mmy3dzf249jk', StampResponse(message='Verify', proof=data.proof, root=data.root, address=data.address, data=data.data, success=data.success)
        )
    else:
        ctx.logger.error("Proof could not be sent")

@agent.on_message(model=VerifyResponse)
async def handle_response(ctx: Context, sender: str, data: VerifyResponse):
    ctx.logger.info(f"Got response from integritas agent: {data.response}")

# Start the agent - this will keep it running and listening for messages
if __name__ == "__main__":
    agent.run()