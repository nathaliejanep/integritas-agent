# Simple Agent - This is a basic example agent that just introduces itself
# It demonstrates the basic structure of a uAgent without any complex functionality

from uagents import Agent, Context
from pydantic import BaseModel, Field
 
# Create a simple agent with a unique name, seed, and endpoint
# This agent runs on port 8000 (same as ai_agent.py, but you'd typically use different ports)
agent = Agent(name="alice", seed="secret_seed_phrase", port=8000, endpoint=["http://localhost:8000/submit"])
class AIRequest(BaseModel):
    question: str = Field(
        description="The question that the user wants to have an answer for."
    )

class AIResponse(BaseModel):
    answer: str = Field(
        description="The answer from AI agent to the user agent"
    )
# Event handler that runs when the agent starts up
@agent.on_event("startup")
# The Context object is a collection of data and functions related to the agent
async def introduce_agent(ctx: Context):
    # The agent executes the function and uses the ctx.logger.info() method to print the message.
    # This will show the agent's name and its unique address
    ctx.logger.info(f"Hello, I'm agent {agent.name} and my address is {agent.address}.")

# Message handler that responds to incoming messages
@agent.on_message(BaseModel)
async def handle_message(ctx: Context, sender: str, message: str):
    # Log the received message
    ctx.logger.info(f"Received message from {sender}: {message}")
    
    # Send a simple test response
    await ctx.send(sender, "Hello! This is a test response from the agent.")
 
# Only run the agent if this file is executed directly (not imported)
if __name__ == "__main__":
    # Start the agent - this will keep it running
    agent.run()
 
