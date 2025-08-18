# protocols/integritas_proto.py
from uagents import Protocol, Model
from typing import Literal, Optional, Dict, Any

IntegritasProtocol = Protocol(name="IntegritasProtocol", version="0.1.0")

# ----- Common -----
class Error(Model):
    code: Literal["BAD_REQUEST","UNAUTHORIZED","NOT_FOUND","TIMEOUT","INTERNAL"]
    message: str

class BaseRequest(Model):
    request_id: str
    # (optional) security / auth metadata
    # nonce: Optional[str]
    # signature: Optional[str]
    # timestamp: Optional[str]

class BaseResponse(Model):
    request_id: str
    ok: bool
    error: Optional[Error] = None

# ----- Stamp Hash -----
class StampHashRequest(BaseRequest):
    hash: str

class StampHashResponse(BaseResponse):
    uid: Optional[str] = None  # set when ok=True

# ----- Verify Proof -----
class VerifyProofRequest(BaseRequest):
    proof: str
    root: str
    address: str
    data: str

class VerifyProofResponse(BaseResponse):
    report: Optional[Dict[str, Any]] = None  # raw API result (or normalized)
