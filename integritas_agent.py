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


# Function to stamp hash using Integritas API
def stamp_hash(hash_value: str, request_id: str = "asi_integritas_agent-request"):
    """
    Send a hash to Integritas API to get it stamped on the blockchain.
    Returns the UID if successful, None if failed.
    """
    try:
        # Prepare the request according to Integritas API docs
        url = f"{INTEGRITAS_BASE_URL}/v1/timestamp/post"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": INTEGRITAS_API_KEY,
            "x-request-id": request_id
        }
        payload = {"hash": hash_value}
        
        # Make the API call
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                uid = data.get("data", {}).get("uid")
                print(f"Hash stamped successfully! UID: {uid}")
                return uid
            else:
                print(f"API returned error: {data.get('message')}")
                return None
        else:
            print(f"API call failed with status {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling Integritas API: {str(e)}")
        return None

# Function to check if hash is onchain by polling the status endpoint
def wait_for_onchain_status(uid: str, max_attempts: int = 10, delay_seconds: int = 10):
    """
    Poll the Integritas API to check if the hash has been confirmed on the blockchain.
    Returns True if onchain, False if failed or timeout.
    """
    try:
        # Prepare the status check request
        url = f"{INTEGRITAS_BASE_URL}/v1/timestamp/status"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": INTEGRITAS_API_KEY
        }
        payload = {
            "uids": [uid]
        }
   
        print(f"Starting to poll for onchain status of UID: {uid}")
        
        for attempt in range(max_attempts):
            
            # Make the status check API call
            response = requests.post(url, headers=headers, json=payload)
            
            print(f"Response status: {response}")

            if response.status_code == 200:
                data = response.json()
                print(f"Response data: {data}")

                if data.get("status") == "success":
                    # Check if the hash is onchain
                    onchain_status = data.get("data")[0].get("onchain", True)
                    print(f"Onchain status: {onchain_status}")

                    if onchain_status:
                        print(f"Polling attempt {attempt + 1}/{max_attempts}")
                        print(f"Hash confirmed onchain! UID: {uid}")
                        # Extract data from response for cleaner return
                        hash_data = data.get("data")[0]
                        return {
                            "onchain": True,
                            "proof": hash_data.get("proof"),
                            "root": hash_data.get("root"),
                            "address": hash_data.get("address"),
                            "data": hash_data.get("data")
                        }
                    else:
                        print(f"Hash not yet onchain. Waiting {delay_seconds} seconds...")
                        time.sleep(delay_seconds)
                        continue
                else:
                    print(f"Status API returned error: {data.get('message')}")
                    return {"onchain": False, "proof": "", "root": "", "address": "", "data": ""}
            else:
                print(f"Status API call failed with status {response.status_code}: {response.text}")
                return {"onchain": False, "proof": "", "root": "", "address": "", "data": ""}
        
        print(f"Timeout waiting for onchain status after {max_attempts} attempts")
        return {"onchain": False, "proof": "", "root": "", "address": "", "data": ""}
        
    except Exception as e:
        print(f"Error checking onchain status: {str(e)}")
        return {"onchain": False, "proof": "", "root": "", "address": "", "data": ""}

def verify_proof(proof: str, root: str, address: str, data: str, request_id: str = "asi_integritas_agent-request"):
    """
    Verify the proof using the Integritas API.
    Returns True if successful, False if failed.
    """
    try:
        # Prepare the request according to Integritas API docs
        url = f"{INTEGRITAS_BASE_URL}/v1/verify/post-lite"
        headers = {
            "x-api-key": INTEGRITAS_API_KEY,
            "x-report-required": "true"
        }
        
        # Create the JSON payload
        payload_data = [{"proof": proof, "root": root, "address": address, "data": data}]
        
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(payload_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Prepare form data with the JSON file
            with open(temp_file_path, 'rb') as json_file:
                files = {'file': ('proof_data.json', json_file, 'application/json')}
                
                # Make the API call with form data
                response = requests.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                response_data = response.json()  
                print(f"Response data: {response_data}")
                return response_data
            else:
                print(f"Verify API call failed with status {response.status_code}: {response.text}")
                return False
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:  
        print(f"Error verifying proof: {str(e)}")
        return False

# 2. Message handler that processes incoming hash data from client agent and sends response back to client
@agent.on_message(model=HashRequest, replies=StampResponse)
async def process_hash(ctx: Context, sender: str, msg: HashRequest):
    # Log the incoming hash and who sent it
    ctx.logger.info(f"Received hash from {sender}: {msg.hash}")
    
    # Try to stamp the hash using Integritas API
    uid = stamp_hash(msg.hash, f"agent-{sender[:8]}")
    
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
            # Send the response back to the agent that sent the hash
            await ctx.send(
                sender, StampResponse(
                    message=response_message, 
                    proof=onchain_result["proof"], 
                    root=onchain_result["root"], 
                    address=onchain_result["address"], 
                    data=onchain_result["data"], 
                    success=True
                )
            )
        else:
            # Hash was submitted but not confirmed onchain within timeout
            response_message = f"Hash submitted but not confirmed onchain within timeout. UID: {uid}"
            ctx.logger.warning(f"Hash not confirmed onchain within timeout. UID: {uid}")
            # Send the response back to the agent that sent the hash
            await ctx.send(
                sender, StampResponse(message=response_message, proof="", root="", address="", data="", success=False)
            )
    else:
        # Stamping failed
        response_message = f"Failed to stamp hash: {msg.hash}"
        ctx.logger.error(f"Failed to stamp hash: {msg.hash}")
        # Send the response back to the agent that sent the hash
        await ctx.send(
            sender, StampResponse(message=response_message, proof="", root="", address="", data="", success=False)
        )


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