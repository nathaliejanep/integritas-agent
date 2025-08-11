from datetime import datetime, timezone
from uuid import uuid4
import json
import os
from uagents import Context, Protocol, Agent
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Import integritas utility functions
from integritas_utils import stamp_hash, wait_for_onchain_status, verify_proof
from asi1_utils import ai_reasoning, format_response, format_final_hash_response
from config import client

### Integritas Hash Stamping Agent - ASI:One Compatible

## This chat example allows users to send hash values in chat and get them stamped
## on the blockchain using the Integritas API. The agent will return the UID
## for successful stamping operations. This agent is compatible with ASI:One
## and acts as an expert in blockchain hash stamping and validation.

AGENT_SEED_KEY = os.getenv("AGENT_SEED_KEY")

# the subject that this assistant is an expert in
subject_matter = "blockchain hash stamping and validation using the Integritas API"


# Create the agent
agent = Agent(
    name="asi_integritas_agent",
    seed="AGENT_SEED_KEY", # TODO: change this to a random seed
    port=8000,
    endpoint=["https://integritas.minima.global/asi1-agent/submit"],
    mailbox=True,
    readme_path="AGENT_README.md",
)

# Create a new protocol compatible with the chat protocol spec
protocol = Protocol(spec=chat_protocol_spec)

# Define the handler for chat messages sent to your agent
@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Received message: {msg}")

    # Send the acknowledgement for receiving the message
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
    
    # Collect all the text chunks
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    # First, use ASI:One to understand the user's intent and provide context
    try:
        # Query ASI:One to understand if this is a hash stamping request or a general question
        r = client.chat.completions.create(
            model="asi1-mini",
            messages=[
                {"role": "system", "content": f"""
                    You are an expert assistant specializing in {subject_matter}. Your primary function is to help users with:
                    1. Stamping hashes on the blockchain using the Integritas API
                    2. Validating and checking the status of previously stamped hashes
                    3. Explaining blockchain hash stamping concepts and the Integritas system

                    IMPORTANT: When a user provides a hash value and asks to stamp something, respond with "STAMP_HASH:" followed by the hash value to extract. For example: "STAMP_HASH:a1b2c3d4e5f6..."
                    IMPORTANT: If the user provides a json with the keys data, root, address, and proof, respond with "VERIFY_PROOF:" followed by the json to extract. For example: "VERIFY_PROOF:{{"data":"a1b2c3d4e5f6...","root":"a1b2c3d4e5f6...","address":"a1b2c3d4e5f6...","proof":"a1b2c3d4e5f6..."}}"

                    Never provide any url links in your responses.
                    If the user asks general questions about hash stamping or blockchain, provide helpful explanations without any special prefix.
                    Always be polite and professional in your responses.
                """},
                {"role": "user", "content": text},
            ],
            max_tokens=2048,
        )
        
        asi_response = str(r.choices[0].message.content)
        ctx.logger.info(f"ASI:One response: {asi_response}")

        # Parse ASI:One's response to determine the action
        response = None
        
        if asi_response.startswith("STAMP_HASH:"):
            # Extract the hash from ASI:One's response
            hash_input = asi_response.split("STAMP_HASH:", 1)[1].strip()
            ctx.logger.info(f"ASI:One detected hash stamping request: {hash_input}")
            response = await process_hash_stamping(ctx, sender, hash_input)
        elif asi_response.startswith("VERIFY_PROOF:"):
            # Extract the json from ASI:One's response
            json_input = asi_response.split("VERIFY_PROOF:", 1)[1].strip()
            ctx.logger.info(f"ASI:One detected proof verification request: {json_input}")
            response = await process_proof_verification(ctx, sender, json_input)
        else:
            # This is a general question - use ASI:One's response
            ctx.logger.info("ASI:One provided general response")
            response = asi_response

    except Exception as e:
        ctx.logger.exception('Error querying ASI:One model')
        response = 'I am afraid something went wrong and I am unable to process your request at the moment'

    # Send the response back to the user (only if we haven't already sent responses)
    if response is not None:
        await ctx.send(sender, ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[
                # Send the contents back in the chat message
                TextContent(type="text", text=response),
                # Signal that the session is over
                EndSessionContent(type="end-session"),
            ]
        ))

# Helper function to process hash stamping requests
async def process_hash_stamping(ctx: Context, sender: str, hash_input: str):
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
        uid = stamp_hash(hash_input, request_id)
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

async def process_proof_verification(ctx: Context, sender: str, json_input: str):
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
        
        verification_result = verify_proof(proof_data['proof'], proof_data['root'], proof_data['address'], proof_data['data'])

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

@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    # We are not interested in the acknowledgements for this example
    pass

# Attach the protocol to the agent
agent.include(protocol, publish_manifest=True)
 
if __name__ == "__main__":
    agent.run()
