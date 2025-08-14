## app.test.py

from uagents import Agent, Context, Model, Protocol
import os
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, TextContent, chat_protocol_spec
)

SEED = os.getenv("TESTING_SEED")

class Message(Model):
    message: str

bob = ("test-agent://agent1qflsarrncdqk759pfmlzxpy945k3vdty2hgkcz9w5fy7umtr306uzpqs4cu")
 
# Create an agent named Alice //RECEIVER
alice = Agent(name="alice", seed=SEED, port=8001, endpoint=["http://localhost:8001/submit"])
protocol = Protocol(name=chat_protocol_spec, version="0.3.0")

print(alice.address)
 
# Define a periodic task for Alice
# @alice.on_interval(period=2.0)
# async def say_hello(ctx: Context):
#     ctx.logger.info(f'hello, my name is {alice.name}')
 
@protocol.on_interval(period=60.0)
async def send_message(ctx: Context):
    # ctx.logger.info(f"Received message from {sender}: {msg.message}")
    ctx.logger.info(f"Triggering Bob")
 
    # send the response
    await ctx.send(bob, Message(message="start"))


# alice.include(proto, publish_manifest=False)
print("OK: include passed")
 
# Run the agent
if __name__ == "__main__":
    alice.include(protocol, publish_manifest=False)
    alice.run()