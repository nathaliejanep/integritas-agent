from openai import OpenAI
import os

ASI_API_KEY = os.getenv("ASI_API_KEY")

# ASI:One client configuration
client = OpenAI(
    # By default, we are using the ASI-1 LLM endpoint and model
    base_url='https://api.asi1.ai/v1',
    
    # You can get an ASI-1 api key by creating an account at https://asi1.ai/dashboard/api-keys
    api_key=ASI_API_KEY,
)
