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

## Usage

### Submit a Claim

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "claim_001",
    "description": "Medical emergency prevented travel",
    "supporting_document": "base64_encoded_image"
  }'
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