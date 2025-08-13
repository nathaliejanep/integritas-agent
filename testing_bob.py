from uagents import Agent, Context, Model
import os
from datetime import datetime, timezone
from uuid import uuid4
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
 
SEED = os.getenv("TESTING_SENDER_SEED")

class Message(Model):
    message: str
 
 
INTEGRITAS_ADDRESS = (
    "test-agent://agent1q0js8ddmxupnrk3nguzg0wkaj7zk2a48vy9py7ycn9n6l9dwj4n3sgtc6rr"
)

hash = "bd6e8d28d9e11180dbc5da26995ca29fe6e6f61a09660c29b05919d6a7239876"
messagePromt = f"Hi there. can you stamp this: {hash}"

# Create an agent named Bob //SENDER
bob = Agent(
    name="bob",
    port=8000,
    seed=SEED,
    endpoint=["http://127.0.0.1:8000/submit"],
)
 
print(bob.address)
 
 
@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):

    ctx.logger.info(f"Received message from {sender}: {msg.message}")
    
    if msg.message == "start":
        await ctx.send(INTEGRITAS_ADDRESS, ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[
                # Send the contents back in the chat message
                TextContent(type="text", text=messagePromt),
                # Signal that the session is over
            ]
        ))
 
 
@bob.on_message(ChatMessage)
async def message_handler(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Received message from {sender}: {msg}")

        # Send the acknowledgement for receiving the message
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
 
 
if __name__ == "__main__":
    bob.run()