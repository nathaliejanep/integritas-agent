import os
from openai import OpenAI
from pydantic import BaseModel

# ASI API Configuration
ASI_API_KEY = os.getenv('ASI_API_KEY')

# Initialize ASI client
client = OpenAI(
    # By default, we are using the ASI-1 LLM endpoint and model
    base_url='https://api.asi1.ai/v1',
    # You can get an ASI-1 api key by creating an account at https://asi1.ai/dashboard/api-keys
    api_key=ASI_API_KEY,
)

# Data models for the agent
class ImageRequest(BaseModel):
    image_description: str

class ImageResponse(BaseModel):
    image_url: str

def generate_image(prompt: str) -> str:
    """
    Generate an image using ASI API's image generation capabilities
    """
    try:
        # Use ASI API for image generation
        response = client.images.generate(
            model="dall-e-3",  # or whatever model ASI supports
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Return the image URL
        return response.data[0].url
        
    except Exception as e:
        print(f"Error generating image: {e}")
        # Return a placeholder or raise the exception
        raise e

def generate_text_response(prompt: str) -> str:
    """
    Generate text response using ASI API's LLM capabilities
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # or whatever model ASI supports
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error generating text response: {e}")
        raise e 