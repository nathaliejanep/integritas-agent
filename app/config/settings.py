import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

ASI_API_KEY = os.getenv("ASI_API_KEY")
INTEGRITAS_API_KEY = os.getenv("INTEGRITAS_API_KEY")
if not ASI_API_KEY:
    raise RuntimeError("ASI_API_KEY missing")
if not INTEGRITAS_API_KEY:
    raise RuntimeError("INTEGRITAS_API_KEY missing")

# Networking
INTEGRITAS_BASE_URL = "https://integritas.minima.global/core"

# Agent
AGENT_SEED = os.getenv("AGENT_SEED", "AGENT_SEED")
AGENT_PORT = int(os.getenv("AGENT_PORT", "AGENT_PORT"))
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT", "AGENT_ENDPOINT")

# Polling
POLL_MAX_ATTEMPTS = int(os.getenv("POLL_MAX_ATTEMPTS", "10"))
POLL_DELAY_SECONDS = int(os.getenv("POLL_DELAY_SECONDS", "10"))

# Subject matter prompt (kept here for clarity)
SUBJECT_MATTER = """blockchain hash stamping and validation using the Integritas API. Your primary function is to help users with:
1) Stamping hashes on the blockchain using the Integritas API
2) Validating and checking the status of previously stamped hashes
3) Explaining blockchain hash stamping concepts and the Integritas system

IMPORTANT: When a user provides a hash and asks to stamp, respond with "STAMP_HASH:<hash>".
IMPORTANT: If the user provides a json with keys data, root, address, proof, respond with "VERIFY_PROOF:<json>".

Never provide any url links in your responses.
"""
