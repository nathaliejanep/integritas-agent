from uagents import Agent, Context, Model
import os

SEED = os.getenv("TESTING_SEED")

class Message(Model):
    message: str

bob = ("test-agent://agent1qflsarrncdqk759pfmlzxpy945k3vdty2hgkcz9w5fy7umtr306uzpqs4cu")
 
# Create an agent named Alice //RECEIVER
alice = Agent(name="alice", seed=SEED, port=8001, endpoint=["http://localhost:8001/submit"])

print(alice.address)
 
# Define a periodic task for Alice
# @alice.on_interval(period=2.0)
# async def say_hello(ctx: Context):
#     ctx.logger.info(f'hello, my name is {alice.name}')
 
@alice.on_interval(period=60.0)
async def send_message(ctx: Context):
    # ctx.logger.info(f"Received message from {sender}: {msg.message}")
    ctx.logger.info(f"Triggering Bob")
 
    # send the response
    await ctx.send(bob, Message(message="start"))
 
# Run the agent
if __name__ == "__main__":
    alice.run()