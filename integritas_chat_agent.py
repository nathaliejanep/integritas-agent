import os
from datetime import datetime
from uuid import uuid4
 
from uagents import Context, Agent
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
)

# Import integritas utility functions
from integritas_utils import stamp_hash, wait_for_onchain_status
from chat_proto import chat_proto
from models import generate_text_response

### Integritas Hash Stamping Agent

## This chat example allows users to send hash values in chat and get them stamped
## on the blockchain using the Integritas API. The agent will return the UID
## for successful stamping operations.

# Agent configuration
AGENT_SEED = os.getenv("AGENT_SEED", "integritas-chat-agent")
AGENT_NAME = os.getenv("AGENT_NAME", "Integritas Chat Agent")
PORT = 8001  # Different port from the image generator agent

# Create the agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=PORT,
    endpoint=f"http://localhost:{PORT}/submit",
)

# Define the handler for chat messages sent to your agent
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """
    STEP 1: MESSAGE RECEIVED
    This function is called when a ChatMessage is received from another agent
    - ctx: Context object containing agent information and logging
    - sender: Address of the agent that sent the message
    - msg: The ChatMessage object containing the actual message content
    """
    ctx.logger.info(f"=== CHAT MESSAGE RECEIVED ===")
    ctx.logger.info(f"From: {sender}")
    ctx.logger.info(f"Message ID: {msg.msg_id}")
    
    # STEP 2: SEND ACKNOWLEDGEMENT
    # Immediately acknowledge receipt of the message to the sender
    ctx.logger.info("Sending acknowledgement back to sender...")
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )

    # STEP 3: EXTRACT TEXT CONTENT
    # Loop through all content items in the message and extract text
    ctx.logger.info("Extracting text content from message...")
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
            ctx.logger.info(f"Found text content: {item.text}")

    # STEP 4: INITIALIZE RESPONSE
    # Set a default error response in case something goes wrong
    response = 'I am afraid something went wrong and I am unable to process your hash at the moment'
    
    try:
        # STEP 5: VALIDATE INPUT
        # Clean the input text (remove whitespace, newlines, etc.)
        ctx.logger.info("Cleaning and validating input...")
        hash_input = text.strip()
        ctx.logger.info(f"Cleaned hash input: '{hash_input}'")
        
        # STEP 6: BASIC VALIDATION
        # Check if the input looks like a valid hash (hex string with minimum length)
        if not hash_input:
            ctx.logger.warning("Empty hash input received")
            response = "Please provide a hash value to stamp."
        elif len(hash_input) < 32:  # Basic length check for hash
            ctx.logger.warning(f"Hash too short: {len(hash_input)} characters (minimum 32)")
            response = "The provided value doesn't appear to be a valid hash. Please provide a proper hash value."
        else:
            # STEP 7: PREPARE FOR STAMPING
            # Generate a unique request ID for tracking this stamping operation
            request_id = f"chat-{sender[:8]}-{int(datetime.now().timestamp())}"
            ctx.logger.info(f"Generated request ID: {request_id}")
            
            # STEP 8: CALL INTEGRITAS API
            # Try to stamp the hash using the Integritas blockchain API
            ctx.logger.info(f"Calling Integritas API to stamp hash: {hash_input}")
            uid = stamp_hash(hash_input, request_id)
            
            # STEP 9: PROCESS STAMPING RESULT
            if uid:
                # SUCCESS: Hash was successfully stamped on the blockchain
                ctx.logger.info(f"✅ Hash stamped successfully! UID: {uid}")
                
                # STEP 10: CREATE BASE RESPONSE
                # Create a basic success response with the UID
                base_response = f"✅ Hash stamped successfully!\n\n**UID:** {uid}\n\nYour hash has been submitted to the blockchain. The UID can be used to track the status of your stamp."
                
                # STEP 11: ENHANCE RESPONSE WITH ASI API (OPTIONAL)
                # Try to use ASI API to generate a more friendly and informative response
                ctx.logger.info("Attempting to enhance response with ASI API...")
                try:
                    enhanced_prompt = f"""
                    You are a helpful blockchain assistant. A user has successfully stamped a hash on the blockchain with UID: {uid}.
                    
                    Provide a friendly, informative response that:
                    1. Confirms the successful stamping
                    2. Explains what the UID means
                    3. Suggests next steps (like how to verify the stamp)
                    4. Keeps it concise and professional
                    
                    Base response: {base_response}
                    """
                    
                    response = generate_text_response(enhanced_prompt)
                    ctx.logger.info("✅ Response enhanced with ASI API")
                except Exception as ai_error:
                    # FALLBACK: If ASI API fails, use the base response
                    ctx.logger.warning(f"ASI API enhancement failed, using base response: {ai_error}")
                    response = base_response
                
            else:
                # FAILURE: Hash stamping failed
                ctx.logger.error("❌ Hash stamping failed - no UID returned")
                response = "❌ Failed to stamp hash. Please check your hash value and try again."
                
    except Exception as e:
        # STEP 12: ERROR HANDLING
        # Catch any unexpected errors during processing
        ctx.logger.exception('Error processing hash stamping request')
        response = f"An error occurred while processing your request: {str(e)}"

    # STEP 13: SEND RESPONSE BACK TO USER
    # Create and send the final response message back to the sender
    ctx.logger.info("Sending response back to user...")
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            # Send the text response (success or error message)
            TextContent(type="text", text=response),
            # Signal that the chat session is over
            EndSessionContent(type="end-session"),
        ]
    ))
    ctx.logger.info("=== CHAT MESSAGE PROCESSING COMPLETE ===")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    # We are not interested in the acknowledgements for this example
    pass

# Include the chat protocol in the agent
agent.include(chat_proto, publish_manifest=True)

# Add REST endpoint for chat at agent level
@agent.on_rest_post("/chat", ChatMessage, ChatMessage)
async def handle_chat_rest(ctx: Context, msg: ChatMessage) -> ChatMessage:
    """
    REST ENDPOINT HANDLER
    This function handles HTTP POST requests to /chat endpoint (e.g., from Postman)
    - ctx: Context object containing agent information and logging
    - msg: The ChatMessage object from the HTTP request body
    - Returns: ChatMessage response that gets sent back as HTTP response
    """
    ctx.logger.info(f"=== REST CHAT REQUEST RECEIVED ===")
    ctx.logger.info(f"Message ID: {msg.msg_id}")
    
    # STEP 1: SET DEFAULT SENDER
    # For REST requests, we use a default sender since there's no actual agent
    sender = "rest-client"
    ctx.logger.info(f"Using default sender: {sender}")

    # STEP 2: EXTRACT TEXT CONTENT
    # Loop through all content items in the message and extract text
    ctx.logger.info("Extracting text content from REST message...")
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
            ctx.logger.info(f"Found text content: {item.text}")

    # STEP 3: INITIALIZE RESPONSE
    # Set a default error response in case something goes wrong
    response = 'I am afraid something went wrong and I am unable to process your hash at the moment'
    
    try:
        # Clean the input text (remove whitespace, newlines, etc.)
        hash_input = text.strip()
        
        # Basic validation - check if it looks like a hash (hex string)
        if not hash_input:
            response = "Please provide a hash value to stamp."
        elif len(hash_input) < 32:  # Basic length check for hash
            response = "The provided value doesn't appear to be a valid hash. Please provide a proper hash value."
        else:
            # Generate a unique request ID
            request_id = f"rest-{int(datetime.now().timestamp())}"
            
            # Try to stamp the hash using Integritas API
            ctx.logger.info(f"Attempting to stamp hash: {hash_input}")
            uid = stamp_hash(hash_input, request_id)
            
            if uid:
                # Hash was successfully submitted - use ASI API to generate enhanced response
                base_response = f"✅ Hash stamped successfully!\n\n**UID:** {uid}\n\nYour hash has been submitted to the blockchain. The UID can be used to track the status of your stamp."
                
                # Use ASI API to enhance the response
                try:
                    enhanced_prompt = f"""
                    You are a helpful blockchain assistant. A user has successfully stamped a hash on the blockchain with UID: {uid}.
                    
                    Provide a friendly, informative response that:
                    1. Confirms the successful stamping
                    2. Explains what the UID means
                    3. Suggests next steps (like how to verify the stamp)
                    4. Keeps it concise and professional
                    
                    Base response: {base_response}
                    """
                    
                    response = generate_text_response(enhanced_prompt)
                except Exception as ai_error:
                    ctx.logger.warning(f"ASI API enhancement failed, using base response: {ai_error}")
                    response = base_response
                
            else:
                response = "❌ Failed to stamp hash. Please check your hash value and try again."
                
    except Exception as e:
        ctx.logger.exception('Error processing hash stamping request')
        response = f"An error occurred while processing your request: {str(e)}"

    # Return the response for REST endpoint
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            # Send the contents back in the chat message
            TextContent(type="text", text=response),
            # Signal that the session is over
            EndSessionContent(type="end-session"),
        ]
    )

if __name__ == "__main__":
    agent.run() 