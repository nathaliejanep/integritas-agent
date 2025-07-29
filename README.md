# Integritas Agent

A multi-agent system for blockchain timestamping and verification using the Integritas API. This project demonstrates how to create autonomous agents that can stamp hashes on the blockchain and verify proofs.

## Overview

The Integritas Agent system consists of multiple uAgents that work together to:

- Submit hashes to the Integritas API for blockchain timestamping
- Wait for onchain confirmation
- Verify proofs using the Integritas verification API
- Provide a complete workflow for hash verification

## Architecture

The system includes several agents:

### 1. Integritas Agent (`integritas_agent.py`)

- **Port**: 8000
- **Purpose**: Main service agent that receives hash data and processes it through the Integritas API
- **Functions**:
  - Stamps hashes on the blockchain
  - Polls for onchain confirmation
  - Verifies proofs
  - Responds to other agents with results

### 2. Client Agent (`client.py`)

- **Port**: 8001
- **Purpose**: Example client that sends hash verification requests
- **Functions**:
  - Sends predefined hash to the Integritas agent
  - Handles responses and forwards results

### 3. Verify Client Agent (`verify_client.py`)

- **Port**: 8002
- **Purpose**: Specialized client for proof verification
- **Functions**:
  - Receives stamped hash data
  - Initiates proof verification
  - Handles verification responses

### 4. Simple Agent (`first_agent.py`)

- **Port**: 8000
- **Purpose**: Basic example agent demonstrating uAgent structure
- **Functions**:
  - Simple message handling
  - Basic agent communication

## Prerequisites

- Python 3.8+
- uAgents framework
- Integritas API key
- Network connectivity to Integritas API

## Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd integritas-agent
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install uagents requests pydantic
   ```

4. **Configure API Key**:
   - Edit `integritas_agent.py`
   - Set your Integritas API key in the `INTEGRITAS_API_KEY` variable
   - For production, use environment variables instead of hardcoding

## Configuration

### API Configuration

The Integritas API configuration is in `integritas_agent.py`:

```python
INTEGRITAS_BASE_URL = "https://integritas.minima.global/core"
INTEGRITAS_API_KEY = "your-api-key-here"  # Set your actual API key
```

### Agent Configuration

Each agent has configurable parameters:

- **Name**: Unique identifier for the agent
- **Seed**: Cryptographic seed for address generation
- **Port**: Network port for the agent
- **Endpoint**: Webhook endpoint for receiving messages

## Usage

### Running the Integritas Agent

1. **Start the main Integritas agent**:

   ```bash
   python integritas_agent.py
   ```

   This will start the service agent on port 8000 and log its address.

2. **Start a client agent** (in a separate terminal):
   ```bash
   python client.py
   ```
   This will send a test hash to the Integritas agent.

### Workflow Example

1. **Hash Submission**: Client agent sends a hash to the Integritas agent
2. **Stamping**: Integritas agent submits the hash to the Integritas API
3. **Confirmation**: Agent polls for onchain confirmation
4. **Response**: Results are sent back to the client
5. **Verification**: Proof can be verified using the verification API

### Example Hash Processing

The system processes hashes through these steps:

1. **Initial Request**: `HashRequest` with hash data
2. **API Submission**: Hash sent to Integritas timestamp API
3. **Status Polling**: Agent checks for onchain confirmation
4. **Response**: `StampResponse` with proof, root, address, and data
5. **Verification**: Optional proof verification step

## API Integration

### Integritas API Endpoints Used

- **POST** `/v1/timestamp/post` - Submit hash for timestamping
- **POST** `/v1/timestamp/status` - Check onchain status
- **POST** `/v1/verify/post-lite` - Verify proofs

### Data Models

#### HashRequest

```python
class HashRequest(BaseModel):
    hash: str = Field(description="The hash data to be processed")
```

#### StampResponse

```python
class StampResponse(BaseModel):
    message: str = Field(description="Response message")
    proof: str = Field(description="Proof from Integritas API")
    root: str = Field(description="Root from Integritas API")
    address: str = Field(description="Address from Integritas API")
    data: str = Field(description="Data from Integritas API")
    success: bool = Field(description="Whether stamping was successful")
```

## Error Handling

The system includes comprehensive error handling:

- API call failures
- Network timeouts
- Invalid responses
- Onchain confirmation timeouts

## Development

### Adding New Agents

1. Create a new Python file following the agent pattern
2. Define your data models using Pydantic
3. Implement message handlers using `@agent.on_message`
4. Configure the agent with unique name, seed, and port

### Testing

1. Start the Integritas agent
2. Run client agents to test the workflow
3. Monitor logs for successful hash processing
4. Verify results using the Integritas API directly

## Security Considerations

- Store API keys securely (use environment variables)
- Validate all incoming data
- Implement rate limiting for API calls
- Use HTTPS for all communications
- Regularly rotate API keys

### Debug Mode

Enable debug logging by modifying the agent configuration:

```python
agent = Agent(name="debug_agent", seed="debug_seed", port=8000, debug=True)
```

## Changelog

### Version 1.0.0

- Initial release
- Basic hash stamping functionality
- Multi-agent communication
- Proof verification support
