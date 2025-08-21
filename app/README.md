# Integritas Agent

## What is the Integritas Agent?

The **Integritas Agent** is an AI-powered assistant that helps you interact with blockchain technology for data integrity and timestamping. It's designed to make blockchain operations simple and accessible through natural conversation.

## What Can This Agent Do?

### 🔐 Hash Stamping

**Stamps your data hashes on the blockchain for permanent proof of existence**

- Upload any hash value and get it permanently recorded on the Minima blockchain
- Receive a unique UID (Unique Identifier) for tracking your stamped data
- Automatic monitoring until your data is confirmed on the blockchain

**Example:**

```
You: "Please stamp this hash: a1b2c3d4e5f6..."
Agent: "✅ Hash stamped successfully! UID: abc123def456..."
```

### 🔍 Proof Verification

**Verifies that your data exists on the blockchain and hasn't been tampered with**

- Verify blockchain proofs with full NFT traceability
- Get detailed verification reports with timestamps and block information
- Confirm data integrity and authenticity

**Example:**

```
You: "Verify this proof: {"data":"...","root":"...","address":"...","proof":"..."}"
Agent: "Proof Verified! Your data was stamped on 2024-01-15..."
```

### AI-Powered Intelligence

**Uses advanced AI to understand your requests and provide helpful explanations**

- Automatically recognizes what you want to do
- Provides clear, professional explanations of blockchain concepts
- Answers questions about hash stamping and data integrity
- Formats responses in an easy-to-understand way

## How to Use the Agent

### Getting Started

1. **Start a conversation** with the agent
2. **Tell it what you want to do** in natural language
3. **Provide the required information** (hash values, proof data, etc.)
4. **Get your results** with detailed explanations

### Common Interactions

#### For Hash Stamping:

- "I want to stamp a hash"
- "Please stamp this hash: [your-hash-value]"
- "Can you help me timestamp my data on the blockchain?"

#### For Proof Verification:

- "Verify this proof"
- "Check if this data is on the blockchain"
- "Is this proof valid?"

#### For General Questions:

- "How does blockchain timestamping work?"
- "What is hash stamping?"
- "Explain data integrity on the blockchain"

## What You'll Get Back

### Hash Stamping Results:

- Confirmation of successful stamping
- Status updates until blockchain confirmation
- Stamp information

### Proof Verification Results:

- Verification status
- Date when data was stamped
- Block number and transaction links
- Detailed verification report

### AI Explanations:

- 📚 Clear explanations of blockchain concepts
- 💡 Practical insights about your data
- 🔍 Analysis of verification results
- 📖 Educational content about data integrity

## Why Use This Agent?

### **Simplicity**

- No technical knowledge required
- Natural language interaction
- Clear, understandable responses

### **Security**

- Professional blockchain integration
- Secure API handling
- No data storage on the agent

### **Efficiency**

- Instant hash stamping
- Real-time status monitoring
- Automated verification processes

### **Intelligence**

- AI-powered understanding
- Context-aware responses
- Professional explanations

## Supported Blockchains

- **Minima Blockchain**: Primary blockchain for hash stamping and verification
- **NFT Traceability**: Full NFT-based proof system
- **Real-time Confirmation**: Automatic on-chain status monitoring

## Use Cases

### 📄 **Document Integrity**

- Prove document existence at a specific time
- Verify documents haven't been altered
- Create permanent timestamps

### 🔐 **Data Authentication**

- Authenticate digital signatures
- Verify data provenance
- Establish data ownership

### ⏰ **Stamp Services**

- Create proof of existence
- Establish priority claims
- Provide stamps

### 🔍 **Audit Trails**

- Track data changes over time
- Maintain verifiable records
- Support compliance requirements

## Technical Requirements

- **API Keys**: Integritas and ASI:One API access
- **Network**: Internet connection for blockchain operations
- **Format**: Standard hash formats (SHA-256, SHA-3, etc.)

## Getting Help

The agent is designed to be self-explanatory, but if you need additional support:

- **Ask the agent directly** - it can explain its own capabilities
- **Check the documentation** - (https://docs.integritas.minima.global)[https://docs.integritas.minima.global]
- **Use natural language** - describe what you want to achieve

---

**Agent Type**: Integritas Blockchain Hash Stamping Agent  
**Primary Function**: Hash stamping and proof verification  
**Interaction Style**: Natural language conversation  
**Blockchain**: Minima with NFT traceability

---

## Agent to agent

Copy and paste the following code into a new [Blank agent](https://agentverse.ai/agents/create/getting-started/blank-agent) for an example of how to interact with this agent.

### Stamping consumer

```
import asyncio
import json
from uagents import Agent, Context, Model
from typing import Literal, Optional
from uuid import uuid4

# ----- Common -----
class Error(Model):
    code: Literal["BAD_REQUEST","UNAUTHORIZED","NOT_FOUND","TIMEOUT","INTERNAL"]
    message: str

class BaseRequest(Model):
    request_id: str

class BaseResponse(Model):
    request_id: str
    ok: bool
    error: Optional[Error] = None

# ----- Stamp Hash -----
class StampHashRequest(BaseRequest):
    hash: str

class StampHashResponse(BaseResponse):
    uid: Optional[str] = None  # set when ok=True

# ----- Status Check -----
class UidRequest(BaseRequest):
    uid: str

class UidResponse(BaseResponse):
    proof: Optional[str] = None
    root: Optional[str] = None
    address: Optional[str] = None
    data: Optional[str] = None

INTEGRITAS_AGENT_ADDRESS = ""

# -----------------------
# Config
# -----------------------
consumer = Agent()

# ENTER THE HASH YOU WISH TO STAMP HERE
HASH_TO_SEND = ""

# -----------------------
# Handlers
# -----------------------
@consumer.on_message(StampHashResponse)
async def on_stamp_resp(ctx: Context, sender: str, msg: StampHashResponse):
    payload = msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
    payload_s = json.dumps(payload, ensure_ascii=False)

    if msg.ok and msg.uid:
        ctx.logger.info(f"Stamp success ✅ uid={msg.uid}")
        # Optional: immediately ask for on-chain status (fire-and-forget)
        await ctx.send(sender, UidRequest(request_id=str(uuid4()), uid=msg.uid))
    else:
        ctx.logger.warning(f"Stamp failed ❌ response={payload_s}")

@consumer.on_message(UidResponse)
async def on_uid_resp(ctx: Context, sender: str, msg: UidResponse):
    payload = msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
    payload_s = json.dumps(payload, ensure_ascii=False)

    if msg.ok:
        ctx.logger.info(f"On-chain ✅ response={payload_s}")
    else:
        ctx.logger.warning(f"Status check failed ❌ response={payload_s}")

# -----------------------
# Helper (fire-and-forget)
# -----------------------
async def stamp_via_provider(ctx: Context, provider_address: str, hash_value: str) -> str:
    """Send a StampHashRequest and return the request_id (no waiting)."""
    request_id = str(uuid4())
    await ctx.send(provider_address, StampHashRequest(request_id=request_id, hash=hash_value))
    return request_id

# -----------------------
# Boot
# -----------------------
@consumer.on_event("startup")
async def go(ctx: Context):
    ctx.logger.info("BOOTING… waiting 10s before starting")
    await asyncio.sleep(10)

    rid = await stamp_via_provider(ctx, INTEGRITAS_AGENT_ADDRESS, HASH_TO_SEND)
    ctx.logger.info(f"Stamp request sent (request_id={rid}). Await async responses in on_stamp_resp/on_uid_resp.")

if __name__ == "__main__":
    consumer.run()
```

### Verifying consumer

```
import asyncio
import json
from uagents import Agent, Context, Model
from typing import Literal, Optional, Dict, Any
from uuid import uuid4

# ----- Common -----
class Error(Model):
    code: Literal["BAD_REQUEST","UNAUTHORIZED","NOT_FOUND","TIMEOUT","INTERNAL"]
    message: str

class BaseRequest(Model):
    request_id: str

class BaseResponse(Model):
    request_id: str
    ok: bool
    error: Optional[Error] = None

# ----- Verify Proof -----
class VerifyProofRequest(BaseRequest):
    proof: str
    root: str
    address: str
    data: str

class VerifyProofResponse(BaseResponse):
    report: Optional[Dict[str, Any]] = None

INTEGRITAS_AGENT_ADDRESS = ""

# -----------------------
# Config
# -----------------------

consumer = Agent()

# ENTER THE PROOF DATA YOU WISH TO VERIFY HERE
PROOF_TO_VERIFY = {
    "proof": "",
    "root": "",
    "data": "",
    "address": "",
}

# -----------------------
# Handlers
# -----------------------
@consumer.on_message(VerifyProofResponse)
async def on_verify_resp(ctx: Context, sender: str, msg: VerifyProofResponse):
    payload = msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
    payload_s = json.dumps(payload, ensure_ascii=False)

    if msg.ok:
        ctx.logger.info(f"Verification success ✅ response={payload_s}")
    else:
        ctx.logger.warning(f"Verification failed ❌ response={payload_s}")


# -----------------------
# Helper
# -----------------------
async def verify_via_provider(ctx: Context, provider_address: str, *, proof) -> str:
    """Fire-and-forget send. Returns the request_id for logging."""
    request_id = str(uuid4())
    await ctx.send(
        provider_address,
        VerifyProofRequest(
            request_id=request_id,
            proof=proof["proof"],
            root=proof["root"],
            address=proof["address"],
            data=proof["data"],
        ),
    )
    return request_id

# -----------------------
# Boot
# -----------------------
@consumer.on_event("startup")
async def go(ctx: Context):
    ctx.logger.info("BOOTING… waiting 10s before starting")
    await asyncio.sleep(10)

    rid = await verify_via_provider(ctx, INTEGRITAS_AGENT_ADDRESS, proof=PROOF_TO_VERIFY)
    ctx.logger.info(f"Verify request sent (request_id={rid}). Await the async response in on_verify_resp.")

if __name__ == "__main__":
    consumer.run()
```
