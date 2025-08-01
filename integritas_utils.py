# Integritas Utility Functions
# This file contains utility functions for interacting with the Integritas API

import os
import requests
import time
import json
import tempfile
from dotenv import load_dotenv

load_dotenv()

# Configuration for the integritas service
INTEGRITAS_BASE_URL = "https://integritas.minima.global/core"
INTEGRITAS_API_KEY = os.getenv("INTEGRITAS_API_KEY")

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