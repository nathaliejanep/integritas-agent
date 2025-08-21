from pydantic import BaseModel
from typing import Any, Dict, List

class StampIntent(BaseModel):
    hash: str

class VerifyIntent(BaseModel):
    data: str
    root: str
    address: str
    proof: str

class IntentResult(BaseModel):
    kind: str  # "STAMP_HASH" | "VERIFY_PROOF" | "GENERAL"
    payload: Dict[str, Any]
    raw_response: str
