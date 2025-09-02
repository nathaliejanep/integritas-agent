import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

ASI_API_KEY = os.getenv("ASI_API_KEY")
INTEGRITAS_API_KEY = os.getenv("INTEGRITAS_API_KEY")
AGENTVERSE_API_KEY = os.getenv("AGENTVERSE_API_KEY")
if not ASI_API_KEY:
    raise RuntimeError("ASI_API_KEY missing")
if not INTEGRITAS_API_KEY:
    raise RuntimeError("INTEGRITAS_API_KEY missing")
if not AGENTVERSE_API_KEY:
    raise RuntimeError("AGENTVERSE_API_KEY missing")


# Networking "https://integritas.minima.global/core"
INTEGRITAS_BASE_URL = "http://localhost:5005"

# Storage
STORAGE_URL = os.getenv("AGENTVERSE_URL", "https://agentverse.ai") + "/v1/storage"

# Agent
AGENT_SEED = os.getenv("AGENT_SEED", "AGENT_SEED")
AGENT_PORT = int(os.getenv("AGENT_PORT", "AGENT_PORT"))
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT", "AGENT_ENDPOINT")

# Polling
POLL_MAX_ATTEMPTS = int(os.getenv("POLL_MAX_ATTEMPTS", "10"))
POLL_DELAY_SECONDS = int(os.getenv("POLL_DELAY_SECONDS", "10"))

# TODO: update prompt to include file hashing and do this in a flow
# Subject matter prompt (kept here for clarity)
SUBJECT_MATTER = """blockchain hash stamping and validation using the Integritas API. Your primary function is to help users with:
1) Stamping hashes on the blockchain using the Integritas API
2) Validating and checking the status of previously stamped hashes
3) Explaining blockchain hash stamping concepts and the Integritas system

IMPORTANT: When a user provides a hash and asks to stamp, respond with "STAMP_HASH:<hash>".
IMPORTANT: If the user uploads a file and asks to stamp the file, respond with "STAMP_FILE:" (no file path needed).
IMPORTANT: If the user uploads a file and asks to hash the file, respond with "HASH_FILE:" (no file path needed).
IMPORTANT: If the user provides a json with keys data, root, address, proof, respond with "VERIFY_PROOF:<json>".
IMPORTANT: If the user uploads a file with any request related to hashing or stamping, prioritize the uploaded file over any file path mentioned.

Never provide any url links in your responses.
"""
