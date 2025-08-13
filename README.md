# Integritas Agent - ASI:One Compatible Blockchain Hash Stamping Agent

## Agent Overview

**Integritas Agent** - is a AI-powered blockchain hash stamping and validation agent that integrates with the [Integritas API](https://integritas.minima.global/) and [ASI:One](https://asi1.ai/) for intelligent blockchain operations.

### Core Functionality

- **Hash Stamping**: Stamps data hashes on the Minima blockchain using Integritas API
- **Proof Verification**: Validates blockchain proofs and NFT traceability
- **AI-Powered Reasoning**: Uses ASI:One for intelligent request processing and response generation
- **Real-time Status Monitoring**: Polls blockchain status until confirmation

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- ASI:One API key ([Get one here](https://asi1.ai/dashboard/api-keys))
- Integritas API key ([Get one here](https://integritas.minima.global/))

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd integritas-agent
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   ```bash
   export AGENT_SEED_KEY="your-agent-seed-key"
   export ASI_API_KEY="your-asi-one-api-key"
   export INTEGRITAS_API_KEY="your-integritas-api-key"
   ```

4. **Run the agent**
   ```bash
   python3 asi_integritas_agent.py
   ```

## 🔧 Configuration

### Environment Variables

- `AGENT_SEED_KEY`: Unique identifier for the agent
- `ASI_API_KEY`: ASI:One API key for AI reasoning
- `INTEGRITAS_API_KEY`: Integritas API key for blockchain operations

### Agent Configuration

- **Name**: `asi_integritas_agent`
- **Port**: 8000
- **Endpoint**: `https://agentverse.ai/v1/submit`
- **Mailbox**: Enabled for message handling

## 📋 Features

### 1. Hash Stamping

The agent can stamp any hash value on the Minima blockchain:

```
User: "Please stamp this hash: a1b2c3d4e5f6..."
Agent: "Hash stamped successfully! UID: abc123..."
```

### 2. Proof Verification

Verify blockchain proofs with NFT traceability:

```
User: "Verify this proof: {"data":"...","root":"...","address":"...","proof":"..."}"
Agent: "Proof Verified! Your data was stamped on 2024-01-15..."
```

### 3. AI-Powered Analysis

ASI:One integration provides intelligent:

- Intent recognition
- Context-aware responses
- Blockchain data analysis
- Professional explanations

### 4. Real-time Monitoring

- Automatic polling of blockchain status
- On-chain confirmation tracking
- Timeout handling with configurable retries

## Architecture

### Core Components

1. **`asi_integritas_agent.py`** - Main agent implementation

   - Chat protocol handler
   - ASI:One integration
   - Request routing and processing

2. **`integritas_utils.py`** - Blockchain operations

   - Hash stamping functions
   - Status polling
   - Proof verification

3. **`asi1_utils.py`** - AI reasoning utilities

   - ASI:One query handling
   - Response formatting
   - Result analysis

4. **`config.py`** - Configuration management

   - ASI:One client setup
   - API key management

5. **`integritas_docs.py`** - API documentation
   - Integritas API reference
   - Endpoint specifications

## 🔌 API Integration

### Integritas API Endpoints Used

- `POST /v1/timestamp/post` - Hash stamping
- `POST /v1/timestamp/status` - Status checking
- `POST /v1/verify` - Proof verification

### ASI:One Integration

- Model: `asi1-mini`
- Base URL: `https://api.asi1.ai/v1`
- Purpose: Intent recognition and response generation

## 💬 Usage Examples

### Hash Stamping

```
User: "I want to stamp the hash of my document"
Agent: "I can help you stamp your hash on the blockchain. Please provide the hash value you'd like to stamp."
```

### Proof Verification

```
User: "Can you verify this blockchain proof?"
Agent: "I'll verify your proof against the blockchain. Please provide the proof data in JSON format."
```

### General Questions

```
User: "How does blockchain hash stamping work?"
Agent: "Blockchain hash stamping creates an immutable timestamp of your data on the blockchain..."
```

## Response Format

### Successful Hash Stamping

```
✅ Hash stamped successfully!
UID: abc123def456...
Status: Processing on blockchain
```

### Successful Proof Verification

```
Proof Verified!

## Verification Report
| Result | full match |
| Date   | 2024-01-15 |
| Block  | 12345 |
| NFT Proof | Verification ID |

Your data was successfully verified on the blockchain...
```

## Development

### Project Structure

```
integritas-agent/
├── asi_integritas_agent.py    # Main agent
├── integritas_utils.py        # Blockchain utilities
├── asi1_utils.py             # AI utilities
├── config.py                 # Configuration
├── integritas_docs.py        # API documentation
├── requirements.txt          # Dependencies
└── README.md                # This file
```

### Dependencies

- `uagents` - Agent framework
- `uagents-core` - Core agent functionality
- `openai` - ASI:One client
- `requests` - HTTP client
- `python-dotenv` - Environment management

## 🔒 Security

- API keys are managed via environment variables
- No hardcoded credentials
- Secure request ID generation
- Error handling for failed operations

## 📞 Support

- **Integritas Documentation**: [https://docs.integritas.minima.global/](https://docs.integritas.minima.global/)
- **ASI:One Documentation**: [https://docs.asi1.ai/docs](https://docs.asi1.ai/docs)
- **Minima Documentation**: [https://docs.minima.global/](https://docs.minima.global/)

---

**Agent Type**: Integritas Blockchain Hash Stamping Agent  
**AI Integration**: ASI:One  
**Blockchain**: Minima  
**Primary Function**: Hash stamping and proof verification  
**Protocol**: Chat-based interaction with blockchain operations
