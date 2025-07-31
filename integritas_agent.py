# Integritas Agent - This agent receives hash data and processes it
# It acts as a service that other agents can send hash data to

import os
from dotenv import load_dotenv
import requests
import time
import json
import tempfile
from pydantic import BaseModel, Field
from uagents import Agent, Context, Protocol, Model

# Import utility functions from separate file
from integritas_utils import stamp_hash, wait_for_onchain_status, verify_proof


load_dotenv()

# Configuration for the integritas service
# Integritas API configuration
INTEGRITAS_BASE_URL = "https://integritas.minima.global/core"
INTEGRITAS_API_KEY = os.getenv("INTEGRITAS_API_KEY")

# Create the integritas agent with a unique name, seed, and endpoint
agent = Agent(name="integritas_agent",
              seed="your seed value",
              port=8000,
              endpoint=["http://127.0.0.1:8000/submit"]
              )
 
 
# Define the data model for incoming hash data from other agents
class HashRequest(BaseModel):
    hash: str = Field(
        description="The hash data that needs to be processed by the integritas agent."
    )
 
 
# Define the data model for responses sent back to other agents
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

# REST endpoint models for Postman integration
class RestHashRequest(Model):
    hash: str = Field(
        description="The hash data that needs to be processed by the integritas agent."
    )

class RestHashResponse(Model):
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
    api_version: int = Field(
        description="API version number",
        default=1
    )
    request_id: str = Field(
        description="Request identifier",
        default=""
    )
    status: str = Field(
        description="Status of the verification (success/failure)",
        default=""
    )
    status_code: int = Field(
        description="HTTP status code",
        default=0
    )
    message: str = Field(
        description="Human-readable message about the verification result",
        default=""
    )
    timestamp: str = Field(
        description="Timestamp of the verification",
        default=""
    )
    data: dict = Field(
        description="The verification data containing file hash, blockchain data, etc.",
        default_factory=dict
    )

# Event handler that runs when the agent starts up
@agent.on_event("startup")
async def print_address(ctx: Context):
    # Log the agent's unique address so other agents know where to send messages
    ctx.logger.info(agent.address)

# Simple GET endpoint to check if agent is running
@agent.on_rest_get("/health", RestHashResponse)
async def handle_health_check(ctx: Context) -> RestHashResponse:
    """
    Simple health check endpoint to verify the agent is running.
    """
    ctx.logger.info("Health check requested")
    return RestHashResponse(
        message="Integritas Agent is running and ready to process hash requests",
        proof="",
        root="",
        address="",
        data="",
        success=True
    )


# # 2. REST endpoint processes incoming hash data from client agent and sends response directly to verify_client
@agent.on_rest_post("/stamp-hash", RestHashRequest, RestHashResponse)
async def handle_rest_stamp_hash(ctx: Context, req: RestHashRequest) -> RestHashResponse:
    """
    REST endpoint to stamp a hash using Integritas API.
    Accepts hash data from Postman and returns the stamping result.
    """
    ctx.logger.info(f"Received REST request to stamp hash: {req.hash}")
    
    # Try to stamp the hash using Integritas API
    uid = stamp_hash(req.hash, f"rest-postman-{int(time.time())}")
    
    if uid:
        # Hash was successfully submitted, now wait for onchain confirmation
        ctx.logger.info(f"Hash submitted with UID: {uid}, waiting for onchain confirmation...")
        
        # Wait for the hash to be confirmed onchain
        onchain_result = wait_for_onchain_status(uid)
        print(f"Onchain result: {onchain_result}")

        if onchain_result["onchain"]:
            # Hash was successfully stamped and confirmed onchain
            response_message = f"Hash stamped and confirmed onchain! UID: {uid}"
            ctx.logger.info(f"Hash confirmed onchain with UID: {uid}")

            verify_client_address = 'agent1qwrv654kc3axm53mp2yc0e22kxafhju8htk2u5sltwez3088tkdrkhxu0er'
            
            await ctx.send(
                verify_client_address, StampResponse(
                    message=response_message, 
                    proof=onchain_result["proof"], 
                    root=onchain_result["root"], 
                    address=onchain_result["address"], 
                    data=onchain_result["data"], 
                    success=True
                )
            )
            return RestHashResponse(
                message=response_message, 
                proof=onchain_result["proof"], 
                root=onchain_result["root"], 
                address=onchain_result["address"], 
                data=onchain_result["data"], 
                success=True
            )
        else:
            # Hash was submitted but not confirmed onchain within timeout
            response_message = f"Hash submitted but not confirmed onchain within timeout. UID: {uid}"
            ctx.logger.warning(f"Hash not confirmed onchain within timeout. UID: {uid}")
            return RestHashResponse(
                message=response_message, 
                proof="", 
                root="", 
                address="", 
                data="", 
                success=False
            )
    else:
        # Stamping failed
        response_message = f"Failed to stamp hash: {req.hash}"
        ctx.logger.error(f"Failed to stamp hash: {req.hash}")
        return RestHashResponse(
            message=response_message, 
            proof="", 
            root="", 
            address="", 
            data="", 
            success=False
        )

# 2. Message handler that processes incoming hash data from client agent and sends response back to client
# @agent.on_message(model=HashRequest, replies=StampResponse)
# async def process_hash(ctx: Context, sender: str, msg: HashRequest):
#     # Log the incoming hash and who sent it
#     ctx.logger.info(f"Received hash from {sender}: {msg.hash}")
    
#     # Try to stamp the hash using Integritas API
#     uid = stamp_hash(msg.hash, f"agent-{sender[:8]}")
    
#     if uid:
#         # Hash was successfully submitted, now wait for onchain confirmation
#         ctx.logger.info(f"Hash submitted with UID: {uid}, waiting for onchain confirmation...")
        
#         # Wait for the hash to be confirmed onchain
#         onchain_result = wait_for_onchain_status(uid)
#         print(f"Onchain result: {onchain_result}")

#         if onchain_result["onchain"]:
#             # Hash was successfully stamped and confirmed onchain
#             response_message = f"Hash stamped and confirmed onchain! UID: {uid}"
#             ctx.logger.info(f"Hash confirmed onchain with UID: {uid}")
#             # Send the response back to the agent that sent the hash
#             await ctx.send(
#                 sender, StampResponse(
#                     message=response_message, 
#                     proof=onchain_result["proof"], 
#                     root=onchain_result["root"], 
#                     address=onchain_result["address"], 
#                     data=onchain_result["data"], 
#                     success=True
#                 )
#             )
#         else:
#             # Hash was submitted but not confirmed onchain within timeout
#             response_message = f"Hash submitted but not confirmed onchain within timeout. UID: {uid}"
#             ctx.logger.warning(f"Hash not confirmed onchain within timeout. UID: {uid}")
#             # Send the response back to the agent that sent the hash
#             await ctx.send(
#                 sender, StampResponse(message=response_message, proof="", root="", address="", data="", success=False)
#             )
#     else:
#         # Stamping failed
#         response_message = f"Failed to stamp hash: {msg.hash}"
#         ctx.logger.error(f"Failed to stamp hash: {msg.hash}")
#         # Send the response back to the agent that sent the hash
#         await ctx.send(
#             sender, StampResponse(message=response_message, proof="", root="", address="", data="", success=False)
#         )


# 5. Message handler that processes stamp response, verifies proof and sends result response back to verify_client if success
@agent.on_message(model=StampResponse, replies=VerifyResponse)
async def handle_response(ctx: Context, sender: str, data: StampResponse):
    # Log the response received from the integritas agent
    ctx.logger.info(f"Got response from integritas agent: {data.message}")
    
    if data.success:
        res = verify_proof(data.proof, data.root, data.address, data.data)
 
        ctx.logger.info(f"Proof: {data.proof} Root: {data.root} Address: {data.address} Data: {data.data}")
        if res and isinstance(res, dict):
            await ctx.send(
                sender, VerifyResponse(
                    api_version=res.get("apiVersion", 1),
                    request_id=f"verify-{sender[:8]}",
                    status="success",
                    status_code=200,
                    message="Proof verification completed successfully",
                    timestamp=res.get("timestamp", ""),
                    data=res.get("data", {})
                )
            )
        else:
            # Verification failed
            await ctx.send(
                sender, VerifyResponse(
                    api_version=1,
                    request_id=f"verify-{sender[:8]}",
                    status="error",
                    status_code=500,
                    message="Proof verification failed",
                    timestamp="",
                    data={}
                )
            )
    else:
        ctx.logger.error("Proof could not be sent")
 
# Start the agent - this will keep it running and listening for messages
agent.run()