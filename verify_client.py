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

# Define the data model for verification requests sent to the integritas agent
class VerifyRequest(BaseModel):
    proof: str = Field(
        description="The proof to verify"
    )
    root: str = Field(
        description="The root to verify"
    )
    address: str = Field(
        description="The address to verify"
    )
    data: str = Field(
        description="The data to verify"
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
    apiVersion: int = Field(
        description="API version number",
        default=1
    )
    requestId: str = Field(
        description="Request ID for tracking"
    )
    status: str = Field(
        description="Status of the verification request"
    )
    statusCode: int = Field(
        description="HTTP status code"
    )
    message: str = Field(
        description="Response message from the verification"
    )
    timestamp: str = Field(
        description="Timestamp of the verification response"
    )
    data: dict = Field(
        description="Verification data containing fileHash, result, blockchain_data, etc."
    )

@agent.on_event("startup")
async def print_address(ctx: Context):
    # Log the agent's unique address so other agents know where to send messages
    ctx.logger.info(f"Verify client agent address: {agent.address}")


@agent.on_message(model=VerifyRequest)
async def handle_verify_request(ctx: Context, sender: str, data: VerifyRequest):
    ctx.logger.info(f"Received verification request from {sender}")
    ctx.logger.info(f"Proof: {data.proof} Root: {data.root} Address: {data.address} Data: {data.data}")
    # Send verification request to integritas agent
    await ctx.send(
        'agent1qdpzrc02a8lnlzaahtdyy3wnaux64pqa22vykp59tx67jx2mmy3dzf249jk', 
        VerifyRequest(proof=data.proof, root=data.root, address=data.address, data=data.data)
    )

@agent.on_message(model=VerifyResponse)
async def handle_verify_response(ctx: Context, sender: str, data: VerifyResponse):
    ctx.logger.info(f"Got verification response from integritas agent: {data.message}")
    ctx.logger.info(f"Status: {data.status}, Status Code: {data.statusCode}")
    ctx.logger.info(f"Request ID: {data.requestId}, Timestamp: {data.timestamp}")
    
    if data.status == "success" and data.statusCode == 200:
        verification_data = data.data.get("response", {})
        file_hash = verification_data.get("fileHash", "N/A")
        result = verification_data.get("data", {}).get("result", "N/A")
        ctx.logger.info(f"Verification successful - File Hash: {file_hash}, Result: {result}")
    else:
        ctx.logger.info("Verification failed")

# Start the agent - this will keep it running and listening for messages
if __name__ == "__main__":
    agent.run()