# Hacker Tiger

Blockchain-governed AI deployment platform for verifiable and secure CI/CD pipelines.

## Project Description

Hacker Tiger is a hybrid deployment-governance system designed to make software release decisions auditable, tamper-evident, and easier to verify.

The project addresses a common CI/CD problem: build and deployment approvals are often spread across mutable logs, manual reviews, scanner output, and chat tools. That makes it difficult to prove:

- what code was reviewed
- what evidence supported the release
- who approved or rejected the deployment
- whether the final outcome can be independently verified later

Hacker Tiger treats each deployment as a governed transaction.

The system combines:

- a Django control plane for deployment orchestration
- a React dashboard for repository submission and monitoring
- off-chain AI and static validation
- a local blockchain-style ledger for deployment history
- an Ethereum smart contract for validator-based governance and auditability

The repository contains the finalized source code for the project, including:

- the smart contract package at the repo root
- the backend and frontend platform under `Hack/deployment-platform/`
- the multi-agent validation system under `Hack/agents/`

## Architecture Summary

Hacker Tiger uses a hybrid architecture.

### Off-Chain Components

These stay off-chain because they are computationally heavy, large, or sensitive:

- AI agent execution
- repository cloning and inspection
- deployment execution
- security and compliance analysis
- health checks
- evidence storage

### On-Chain Components

These are recorded on Ethereum for governance and auditability:

- validator registration
- validation session creation
- one-vote-per-validator enforcement
- quorum-based finalization
- immutable event emission

## Repository Structure

```text
.
├── contracts/                              # Solidity contracts
├── scripts/                                # Hardhat deployment scripts
├── test/                                   # Hardhat contract tests
├── hardhat.config.js                       # Root Hardhat config
├── package.json                            # Root smart contract package
├── SEPOLIA_DEPLOYMENT_RUNBOOK.md           # Detailed Sepolia deployment runbook
├── docs/                                   # Final reports and supporting docs
├── Hack/
│   ├── agents/                             # Multi-agent validation system
│   └── deployment-platform/
│       ├── backend/                        # Django backend
│       └── deployment-dashboard/           # React frontend
```

## Dependencies

### Core Requirements

- Node.js 18+ recommended
- npm
- Python 3.10+ recommended
- Git

### Smart Contract Package

- Hardhat
- Solidity `0.8.20`
- `@nomicfoundation/hardhat-toolbox`
- `dotenv`

These are installed through the root `package.json`.

### Backend

- Django
- django-cors-headers
- requests
- python-dotenv
- cryptography
- google-generativeai

These are installed through:

- `Hack/deployment-platform/backend/requirements.txt`

### Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- shadcn-ui and related UI dependencies

These are installed through:

- `Hack/deployment-platform/deployment-dashboard/package.json`

### Optional / Demo Dependencies

- Docker and docker-compose for local deployment experiments
- Google Gemini API key(s) for AI-assisted validation
- MetaMask wallet for Ethereum Sepolia deployment
- Alchemy Sepolia RPC endpoint

## Environment Configuration

### Root Smart Contract `.env`

Create:

```bash
cp .env.example .env
```

Set:

```bash
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your-key
ETH_PRIVATE_KEY=0xyourprivatekey
```

### Backend `.env`

Create:

```bash
cp Hack/deployment-platform/backend/.env.example Hack/deployment-platform/backend/.env
```

Important variables:

```bash
DJANGO_SECRET_KEY=your-secret
DEBUG=True
GEMINI_API_KEYS=your_key_1,your_key_2
GEMINI_API_KEY=your_key_1
BLOCKCHAIN_NETWORK=sepolia
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your-key
DEPLOYMENT_VALIDATOR_ADDRESS=0xYourContractAddress
```

### Frontend `.env`

Create:

```bash
cp Hack/deployment-platform/deployment-dashboard/.env.example Hack/deployment-platform/deployment-dashboard/.env
```

Set:

```bash
VITE_API_BASE=http://127.0.0.1:8000/api
VITE_SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your-key
VITE_CONTRACT_ADDRESS=0xYourContractAddress
```

## Setup Instructions

## 1. Smart Contract Package

From the repo root:

```bash
npm install
npx hardhat compile
npm test
```

This verifies the Solidity contracts and the contract test suite.

## 2. Backend Setup

```bash
cd Hack/deployment-platform/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py check
```

## 3. Frontend Setup

```bash
cd Hack/deployment-platform/deployment-dashboard
npm install
npm run build
```

## How to Run the System

### Start the Backend

```bash
cd Hack/deployment-platform/backend
source .venv/bin/activate
python3 manage.py runserver
```

Backend URLs:

- `http://127.0.0.1:8000/api/status/`
- `http://127.0.0.1:8000/api/history/`
- `http://127.0.0.1:8000/blockchain/`
- `http://127.0.0.1:8000/deploy/`

### Start the Frontend

Open a second terminal:

```bash
cd Hack/deployment-platform/deployment-dashboard
npm run dev
```

Frontend URL:

- `http://127.0.0.1:5173`

## How to Use the System

### Frontend Demo Flow

1. Open the React dashboard at `http://127.0.0.1:5173`
2. Enter a GitHub repository URL
3. Submit the repository for validation or deployment
4. Watch the backend-driven blockchain status and deployment results

### Backend Monitor Flow

1. Open `http://127.0.0.1:8000/blockchain/`
2. Review:
   - total blocks
   - valid blocks
   - timed blocks
   - deployment blocks
   - currently active block
3. The active timed block rotates automatically in the backend

### API Flow

The frontend communicates with the Django backend using:

- `GET /api/status/`
- `POST /api/validate/`
- `POST /api/deploy/`
- `GET /api/history/`

## How to Deploy the Smart Contract

The finalized deployment target for this project is Ethereum Sepolia.

### Local Verification Before Deployment

From the repo root:

```bash
npx hardhat compile
npm test
```

### Deploy to Sepolia

Once `SEPOLIA_RPC_URL` and `ETH_PRIVATE_KEY` are configured and the wallet is funded with Sepolia ETH:

```bash
npm run deploy:sepolia
```

Expected output includes:

- deployer wallet address
- deployed contract address
- Sepolia Etherscan URL

The deployment script also writes:

- `deployed-address.json`

After deployment, copy the deployed contract address into:

- `Hack/deployment-platform/backend/.env`
- `Hack/deployment-platform/deployment-dashboard/.env`

or rely on the backend’s fallback resolution from `deployed-address.json`.

### Detailed Deployment Instructions

For the full Ethereum Sepolia workflow, see:

- [SEPOLIA_DEPLOYMENT_RUNBOOK.md](/Users/ashishrajshekhar/Desktop/Team18_2026SpringB_CSE-540_HackerTiger_Project-Smart_Contract_Design/SEPOLIA_DEPLOYMENT_RUNBOOK.md)

## Finalized Source Code

This repository contains the finalized source code submission for the project.

### Smart Contract Source

- `contracts/IValidationLedger.sol`
- `contracts/DeploymentValidationLedger.sol`
- `scripts/deploy.js`
- `test/DeploymentValidationLedger.test.js`

### Backend Source

- `Hack/deployment-platform/backend/deploy/`
- `Hack/deployment-platform/backend/deployer/`

### Frontend Source

- `Hack/deployment-platform/deployment-dashboard/src/`

### Agent System Source

- `Hack/agents/`

## Verification Status

The project was verified with:

- successful Hardhat compile
- passing contract tests
- successful Django `manage.py check`
- successful Django migrations
- successful frontend production build
- successful Sepolia smart contract deployment

## Deployed Contract

The current deployed Sepolia contract is:

- Contract address: `0x7C6F649CC08f012A93bce03D7B546c3448376F83`
- Etherscan: `https://sepolia.etherscan.io/address/0x7C6F649CC08f012A93bce03D7B546c3448376F83`

## Additional Documentation

- `docs/final_Deployment.md`
- `SEPOLIA_DEPLOYMENT_RUNBOOK.md`
- `Hack/deployment-platform/README.md`
- `Hack/deployment-platform/backend/README.md`
- `Hack/deployment-platform/deployment-dashboard/README.md`

## Notes

- The blockchain monitor rotation worker starts when Django starts, so restart the backend after code changes.
- The system uses a hybrid design: off-chain analysis and deployment, on-chain governance and auditability.
- Sepolia is used because it is free and appropriate for academic demonstration.
