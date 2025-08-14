from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class StampResponse(BaseModel):
    uid: str

class OnChainStatus(BaseModel):
    onchain: bool
    proof: Optional[str] = ""
    root: Optional[str] = ""
    address: Optional[str] = ""
    data: Optional[str] = ""

class VerifyInput(BaseModel):
    proof: str
    root: str
    address: str
    data: str

class VerifyReport(BaseModel):
    status: str
    status_code: int
    message: str
    data: Dict[str, Any]
