# Integritas Utility Functions
# This file contains utility functions for interacting with the Integritas API

import os
import requests
import time
import json
import tempfile
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
from uagents import Context, Protocol, Agent
from asi1_utils import ai_reasoning, format_response, format_final_hash_response

load_dotenv()

# Configuration for the integritas service
INTEGRITAS_BASE_URL = "https://integritas.minima.global/core"
INTEGRITAS_API_KEY = os.getenv("INTEGRITAS_API_KEY")

async def process_stamp_hash(ctx: Context, sender: str, hash_input: str):
    """Process hash stamping requests using Integritas API"""
    try:
        # Basic validation - check if it looks like a hash (hex string)
        if not hash_input:
            return "Please provide a hash value to stamp."
        elif len(hash_input) < 32:  # Basic length check for hash
            return "The provided value doesn't appear to be a valid hash. Please provide a proper hash value."
        
        # Generate a unique request ID
        request_id = f"chat-{sender[:8]}-{int(datetime.now().timestamp())}"
        
        # Try to stamp the hash using Integritas API
        ctx.logger.info(f"Attempting to stamp hash: {hash_input}")
        uid = await stamp_hash(hash_input, request_id)
        print('Response from stamping hash', uid)
        
        if uid:
            # Hash was successfully submitted - send initial response
            initial_response = f"✅ Hash stamped successfully!\n\n**UID:** {uid}\n\nYour hash has been submitted to the blockchain. Now checking for onchain confirmation..."
            
            # Send the initial response
            await ctx.send(sender, ChatMessage(
                timestamp=datetime.now(timezone.utc),
                msg_id=uuid4(),
                content=[
                    TextContent(type="text", text=initial_response),
                ]
            ))
            
            # Wait for onchain confirmation
            ctx.logger.info(f"Waiting for onchain confirmation for UID: {uid}")
            onchain_result = await wait_for_onchain_status(uid, ctx, sender)
            
            if onchain_result["onchain"]:
                # Create proof data object
                proof_data = {
                    "proof": onchain_result['proof'],
                    "address": onchain_result['address'],
                    "root": onchain_result['root'],
                    "data": onchain_result['data'],
                }
                
                # Store the proof data in agent's storage using UID as key
                # storage_key = f"proof_{uid}"
                # ctx.storage.set(storage_key, proof_data)
                
                # Log the stored data for verification
                # ctx.logger.info(f"Stored proof data for UID {uid}: {ctx.storage.get(storage_key)}")
                
             
                
                final_hash_response = format_final_hash_response(proof_data)
                
            else:
                final_hash_response = f"⏳ **Status Update**\n\n**UID:** {uid}\n\nYour hash has been submitted but is still waiting for blockchain confirmation. You can check the status later using this UID."
            
            # Send the final response
            await ctx.send(sender, ChatMessage(
                timestamp=datetime.now(timezone.utc),
                msg_id=uuid4(),
                content=[
                    TextContent(type="text", text=final_hash_response),
                    EndSessionContent(type="end-session"),
                ]
            ))
            return None  # Signal that we've already sent responses
            
        else:
            return "❌ Failed to stamp hash. Please check your hash value and try again."
            
    except Exception as e:
        ctx.logger.exception('Error processing hash stamping request')
        return f"An error occurred while processing your request: {str(e)}"

async def stamp_hash(hash_value: str, request_id: str = "asi_integritas_agent-request"):
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

async def wait_for_onchain_status(uid: str, ctx, sender, max_attempts: int = 10, delay_seconds: int = 10):
    print(f"max_attempts={max_attempts} ({type(max_attempts)}), delay_seconds={delay_seconds} ({type(delay_seconds)})")
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
                        wait_response = f"Hash not yet onchain. Waiting {delay_seconds} seconds..."
                        await ctx.send(sender, ChatMessage(
                                timestamp=datetime.now(timezone.utc),
                                msg_id=uuid4(),
                                content=[
                                    TextContent(type="text", text=wait_response),
                                ]
            ))
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
        print(f"Error checking onchain status: {(e)}")
        return {"onchain": False, "proof": "", "root": "", "address": "", "data": ""}
    
async def process_verify_proof(ctx: Context, sender: str, json_input: str):
    """Process proof verification requests using Integritas API"""
    try:
        # Basic validation - check if it looks like a valid json
        if not json_input:
            return "Please provide a valid json with the keys data, root, address, and proof."
        elif not all(key in json_input for key in ["data", "root", "address", "proof"]):
            return "The provided json is missing required keys. Please provide a valid json with the keys data, root, address, and proof."
            
        # Parse the json
        proof_data = json.loads(json_input)
        ctx.logger.info(f"Parsed proof data: {proof_data}")
        
        # Verify the proof using Integritas API
        ctx.logger.info(f"Attempting to verify proof: {proof_data}")
        
        verification_result = await verify_proof(proof_data['proof'], proof_data['root'], proof_data['address'], proof_data['data'])

        print('Response from verifying proof', verification_result)
        
        if verification_result:     
            ctx.logger.info(f"Proof verified successfully")

            ai_reason_response = await ai_reasoning(ctx, sender, verification_result)
            
            final_response = format_response(verification_result, ai_reason_response)
            
            # Send the final response
            await ctx.send(sender, ChatMessage(
                timestamp=datetime.now(timezone.utc),
                msg_id=uuid4(),
                content=[
                    TextContent(type="text", text=final_response),
                    EndSessionContent(type="end-session"),
                ]   
            ))
            return None  # Signal that we've already sent responses
            
        else:
            return "❌ Failed to verify proof. Please check your proof data and try again."
            
    except Exception as e:
        ctx.logger.exception('Error processing proof verification request')
        return f"An error occurred while processing your request: {str(e)}"

async def verify_proof(proof: str, root: str, address: str, data: str, request_id: str = "asi_integritas_agent-request"):
    """
    Verify the proof using the Integritas API.
    Returns True if successful, False if failed.
    """
    try:
        # Prepare the request according to Integritas API docs
        url = f"{INTEGRITAS_BASE_URL}/v1/verify/post-lite"
        headers = {
            "x-api-key": INTEGRITAS_API_KEY,
            "x-report-required": "true",
            "x-request-id": request_id
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