# Blockchain-Governed AI Deployment Platform

Secure, AI-assisted deployment of GitHub repositories with a tamper-evident audit trail. The system evaluates incoming code via static checks and optional Gemini AI validation, writes an immutable record to a blockchain-like ledger, and auto-deploys static websites or built artifacts for live preview.

## Tech Stack

- Backend: Django 4 (Python 3), SQLite, Django Templates
- APIs: Django views + JSON endpoints, CORS enabled
- Frontend (server-rendered): HTML/CSS via Django templates
- Optional AI: Google Gemini (via `google-generativeai`) for code diff risk scoring
- Process Management: Python `http.server` for live serving; subprocess orchestration for cloning and serving
- Security: Encrypted audit evidence using Fernet (symmetric encryption)
- Infra: Local filesystem deployments under `deployment-platform/backend/deployments/`, easy cleanup/rotation

## Repository Structure

- `agents/` — Multi-agent validation service used by the backend's `ai_code_validator` hook in `deployment-platform/backend/deploy/services.py`.
  - `main.py` spins up the `MultiAgentValidator` orchestrator that fans out to the specialized agents under `agents/agents/`.
  - `utils/` contains config loading, Gemini client helpers, and the shared session/audit logging stack consumed whenever a deployment is analyzed.
  - `requirements.txt` and `env.example` define the runtime used by the Django backend before it records a block.
- `deployment-platform/` — Application layer that exposes the APIs and UI.
  - `backend/` — Production Django project (`manage.py`, `deployer/`, `deploy/`). `deploy/services.py` houses the entire pipeline: it validates GitHub repos, calls the agents package, writes blockchain blocks, and launches the local HTTP servers that ultimately serve `deployments/`.
  - `deployment-dashboard/` — React + Vite dashboard that surfaces the blockchain status, deployment history, and repo validation against the Django API (`src/services/blockchainApi.ts`).
  - `Integration_Summary.md` explains how these two pieces talk to each other over `/api/*` routes.

The legacy top-level `hackathon/` scaffolding has been removed; the active pipeline now lives solely under `agents/` and `deployment-platform/`.

## Core Concepts

- Blockchain-like Ledger:
  - Each deployment creates a `Block` with `block_hash`, `parent_hash`, `block_number`, validity flags, timings, and encrypted evidence.
  - Evidence includes static check results, AI verdict, combined score, timestamp (encrypted via Fernet).
  - Timed blocks are created to maintain continuity and support rotation.
- Risk Analysis and Policy:
  - Static quick checks: secrets, `eval/exec`, `curl|bash` patterns.
  - Optional Gemini analysis returns pass/issue list/severity; combined score = 0.7×AI + 0.3×static; threshold 0.6.
  - Combined score decides: accept (deploy) vs quarantine + rollback to last valid.
- Deployment Strategies:
  - HTML-first detection (root or common subdirs), Node.js build folders, static site generators; otherwise generate a documentation showcase page.
  - Starts a per-deployment HTTP server, records port/PID, verifies health, and exposes a local URL.

## Key Endpoints

- UI
  - `GET /` → redirects to `deploy/`
  - `GET /deploy/` → main form UI for GitHub URL + optional token
  - `GET /blockchain/` → human-readable blockchain status dashboard
- APIs
  - `GET /api/status/`
  - `POST /api/validate/` body: `{ "repo_url": "https://github.com/owner/repo" }`
  - `POST /api/deploy/` body: `{ "repo_url": "...", "commit_hash": "..." }`
  - `GET /api/history/`
  - `GET /api/deployment/<deployment_id>/`

## Typical Workflow

1. User enters GitHub repo URL in UI (or calls `POST /api/deploy/`).
2. System validates the repo URL and fetches a diff/README.
3. Risk analysis runs:
   - Static checks + optional Gemini AI
   - Evidence encrypted and stored in `Block`
   - Combined score decides path
4. If accepted:
   - Any existing active block is deactivated
   - New `Block` is marked valid and active
   - Repo is cloned shallowly; site contents detected and served
   - A local URL is returned and shown in UI
5. If rejected:
   - Block marked quarantined, previous valid deployment is rolled back
6. Background lifecycle:
   - Old deployments are cleaned automatically
   - Timed blocks maintain blockchain continuity and rotation (10 minutes)

## Running Locally

### Prerequisites
- Python 3.10+
- Git
- Optional: Google Gemini API key for AI analysis

### Setup

```bash
cd deployment-platform/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

- Optional environment:
  - `DJANGO_SECRET_KEY` (defaults in dev)
  - `FERNET_KEY` (auto-generated in dev)
  - `GEMINI_API_KEY` (enables AI validation)

Visit:
- Web UI: http://127.0.0.1:8000/deploy/
- Blockchain status: http://127.0.0.1:8000/blockchain/
- APIs base: http://127.0.0.1:8000/api/

## Security Notes

- Demo-mode encryption key generation: For production, provide a stable `FERNET_KEY` and secure `SECRET_KEY`.
- CORS is broadly open in `DEBUG` for local integration—lock this down in production.
- Subprocess-based serving is intended for hackathon/demo use, not hardened production.

## What Was Built

- End-to-end gated deployment flow with on-chain audit:
  - Repo validation → AI/static risk scoring → encrypted evidence
  - Block creation with parent linkage, active/valid flags, rotation support
  - Automated deployment for static/Node.js/static-generator repos with health checks
  - Human UI + JSON APIs for both dev and demo needs
- Operational quality-of-life:
  - Cleanup of old deployments and process tracking
  - Rollback capability to last valid block
  - Timed block creation to ensure ledger continuity


