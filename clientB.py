from uagents import Agent, Context, Model
import os

SEED = os.getenv("TESTING_SEED")

class Message(Model):
    message: str

clientA = ("test-agent://agent1qflsarrncdqk759pfmlzxpy945k3vdty2hgkcz9w5fy7umtr306uzpqs4cu")
 
# Create an agent named Alice //RECEIVER
clientB = Agent(name="clientB", seed=SEED, port=8001, endpoint=["http://localhost:8001/submit"])

print(clientB.address)
 
@clientB.on_interval(period=60.0)
async def send_message(ctx: Context):
    # ctx.logger.info(f"Received message from {sender}: {msg.message}")
    ctx.logger.info(f"Triggering ClientA")
 
    # send the response
    await ctx.send(clientA, Message(message="start"))
 
# Run the agent
if __name__ == "__main__":
    clientB.run()