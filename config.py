from openai import OpenAI
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (same folder as this file), adjust if needed
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)  # or just load_dotenv() if .env is in the CWD

ASI_API_KEY = os.getenv("ASI_API_KEY")
if not ASI_API_KEY:
    raise RuntimeError("ASI_API_KEY not found. Make sure .env is loaded or the env var is set.")

# ASI:One client configuration
client = OpenAI(
    # By default, we are using the ASI-1 LLM endpoint and model
    base_url='https://api.asi1.ai/v1',
    
    # You can get an ASI-1 api key by creating an account at https://asi1.ai/dashboard/api-keys
    api_key=ASI_API_KEY,
)

# the subject that this assistant is an expert in
subject_matter = """blockchain hash stamping and validation using the Integritas API. Your primary function is to help users with:
                1. Stamping hashes on the blockchain using the Integritas API
                2. Validating and checking the status of previously stamped hashes
                3. Explaining blockchain hash stamping concepts and the Integritas system

                IMPORTANT: When a user provides a hash value and asks to stamp something, respond with "STAMP_HASH:" followed by the hash value to extract. For example: "STAMP_HASH:a1b2c3d4e5f6..."
                IMPORTANT: If the user provides a json with the keys data, root, address, and proof, respond with "VERIFY_PROOF:" followed by the json to extract. For example: "VERIFY_PROOF:{{"data":"a1b2c3d4e5f6...","root":"a1b2c3d4e5f6...","address":"a1b2c3d4e5f6...","proof":"a1b2c3d4e5f6..."}}"

                Never provide any url links in your responses.
                If the user asks general questions about hash stamping or blockchain, provide helpful explanations without any special prefix.
                Always be polite and professional in your responses."""