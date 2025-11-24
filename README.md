# Claims Automation Agent

An AI-powered insurance claims processing system that automates the evaluation of CFSR (Cancellation For Specific Reason) policy claims using vision analysis and intelligent decision-making.

## Features

- **Automated Claim Processing**: Evaluates insurance claims against policy rules
- **Document Analysis**: Uses vision AI to extract information from medical certificates and supporting documents
- **Multi-Decision Support**: Returns APPROVE, DENY, or UNCERTAIN decisions with detailed explanations
- **RESTful API**: FastAPI-based backend for claim submission and processing
- **Persistent Storage**: PostgreSQL for claim records, MinIO for document storage

## Architecture

- **Agent**: LangChain-based AI agent with custom tools for policy retrieval, metadata extraction, and document analysis
- **API**: FastAPI service for claim submission and status retrieval
- **Storage**: PostgreSQL database and MinIO object storage
- **Evaluation**: Automated testing framework to measure decision accuracy

## Quick Start

### Prerequisites

- Docker
- Python 3.9+
- Python 3.12(Docker)
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Singh8899/claims-automation-agent.git
cd claims-automation-agent
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your credentials
```

3. Start services with Docker Compose:
```bash
docker compose up -d
```

The API will be available at `http://localhost:8000`

## API Usage

### 1. Submit a Claim

Submit a new insurance claim with description, metadata, and optional image:

```bash
curl -X POST http://localhost:8000/claims \
  -F "claim_message=@description.txt" \
  -F "claim_metadata=@metadata.md" \
  -F "claim_image=@supporting_image.jpg"
```

Response:
```json
{
  "message": "Claim submitted successfully",
  "claim_id": "uuid-claim-id",
  "decision": "APPROVE|DENY|UNCERTAIN",
  "explanation": "Detailed explanation of the decision"
}
```

### 2. Get Claim Result

Retrieve the decision and explanation for a specific claim:

```bash
curl -X GET http://localhost:8000/claims/{claim_id}
```

Response:
```json
{
  "decision": "APPROVE|DENY|UNCERTAIN",
  "explanation": "Detailed explanation of the decision"
}
```

### 3. List All Claims

Get a paginated list of all claim IDs:

```bash
curl -X GET "http://localhost:8000/claims?skip=0&limit=100"
```

Response:
```json
{
  "claims": ["claim_id_1", "claim_id_2", "claim_id_3"]
}
```

## Evaluation

Run the evaluation script to test the agent against the test dataset:

```bash
python scripts/evaluate.py
```

Results will be saved to `results/eval_results.json` with accuracy metrics and per-claim analysis.

## Project Structure

```
├── src/
│   ├── agent/          # AI agent logic and prompts
│   ├── api/            # FastAPI application
│   ├── minio/          # Object storage client
│   ├── postgreql/      # Database models and operations
│   └── utils/          # Vision analyzer and utilities
├── scripts/            # Evaluation and server scripts
├── docker/             # Docker configuration
└── takehome-test-data/ # Test claims dataset
```

## License

MIT License - see [LICENSE](LICENSE) file for details