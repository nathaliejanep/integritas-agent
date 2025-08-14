## agent.py

import os
from datetime import datetime, timezone
from uuid import uuid4
from uagents import Context, Protocol, Agent, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Import integritas utility functions
from integritas_utils import process_stamp_hash, process_verify_proof
from config import client, subject_matter

### Integritas Hash Stamping Agent - ASI:One Compatible

## This chat example allows users to send hash values in chat and get them stamped
## on the blockchain using the Integritas API. The agent will return the UID
## for successful stamping operations. This agent is compatible with ASI:One
## and acts as an expert in blockchain hash stamping and validation.

SEED = os.getenv("AGENT_SEED")

# Create the agent
agent = Agent(
    name="asi_integritas_agent",
    # seed=SEED,
    seed="testing_seedai9uf98afs",
    port=8000,
    # endpoint=["https://agentverse.ai/v1/submit"],
    endpoint=["http://127.0.0.1:8000/submit"],
    # mailbox=True,
    # readme_path="README.md",
    # network="mainnet"
)

struct_output_client_proto = Protocol(
    name="StructuredOutputClientProtocol", version="0.1.0"
)


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
    # text = ''
    # for item in msg.content:
    #     if isinstance(item, TextContent):
    #         text += item.text

        # If this is a start-session message, skip further processing
    if any(isinstance(item, StartSessionContent) for item in msg.content):
        ctx.logger.info("StartSessionContent detected — skipping processing.")
        return  # exit the handler here

    # Collect all the text chunks into one string
    text = ''.join(
        item.text for item in msg.content if isinstance(item, TextContent)
    )
    
    # First, use ASI:One to understand the user's intent and provide context
    try:
        # Query ASI:One to understand if this is a hash stamping request or a general question
        r = client.chat.completions.create(
            model="asi1-mini",
            messages=[
                {"role": "system", "content": f"""
                    You are an expert assistant specializing in {subject_matter}. 
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
                # EndSessionContent(type="end-session"),
            ]
        ))

# Helper function to process hash stamping requests
async def process_hash_stamping(ctx: Context, sender: str, hash_input: str):
    await process_stamp_hash(ctx, sender, hash_input)
    

async def process_proof_verification(ctx: Context, sender: str, json_input: str):
    await process_verify_proof(ctx, sender, json_input)

@struct_output_client_proto.on_message(HashRequest)
async def handle_hash_request(
    ctx: Context, sender: str, msg: HashRequest
    ):
    ctx.logger.info(
        f"Got an StructuredOutputResponse from {sender} for {msg}"
    )

@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    # We are not interested in the acknowledgements for this example
        ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )
    # pass TESTING TO PASS THIS

# Attach the protocol to the agent
print("Spec:", chat_protocol_spec.name, chat_protocol_spec.version)
agent.include(protocol, publish_manifest=True)
agent.include(struct_output_client_proto, publish_manifest=True)
 
if __name__ == "__main__":
    agent.run()
