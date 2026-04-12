# Jango Application Stack

The `deployment-platform/` directory houses both halves of the deployment experience:
1. A Django backend that records blockchain blocks, runs the agents, and serves deployments.
2. A React dashboard (Starfall Evolve) that consumes those APIs for repo validation, deployment, and monitoring.

## Folder Overview

- `backend/` – Production Django project. `manage.py` bootstraps the site, `deployer/` holds global settings/URLs, and the `deploy/` app contains all models, services, API views, and templates.
- `deployment-dashboard/` – Vite + React frontend. `src/services/blockchainApi.ts` is the API adapter, while `src/components/*` and `src/pages/*` implement the UX for validation and deployment management.
- `Integration_Summary.md` – Design note describing how the Django APIs and the React UI interact.

Each subfolder has its own README with setup details. The sections below summarize the most important scripts/components and how they work together inside the pipeline.

## Backend (`deployment-platform/backend`)

### Purpose
The Django project exposes `/api/*` endpoints, renders the legacy HTML form at `/deploy/`, launches/monitors local deployment servers, and records every decision in the `Block` model. Before a deployment is marked "valid", it shells into the `agents/` workspace via `deploy/services.py::ai_code_validator()`.

### Main Components
- `manage.py` – Entry point for all Django management commands (migrations, admin user creation, maintenance jobs).
- `deployer/settings.py` – Core configuration (SQLite DB, corsheaders, installed apps, env-driven Gemini key support) plus CORS and logging settings used by both React and HTML clients.
- `deploy/models.py` – Defines the blockchain `Block` plus any auxiliary tables for deployment logs.
- `deploy/services.py` – Pipeline brain: validates GitHub repos, fetches diffs/README snippets, calls the agents, provisions local HTTP servers, tracks process metadata, and cleans up expired deployments.
- `deploy/api_views.py` & `api_urls.py` – REST surface consumed by the frontend (`/api/status/`, `/api/validate/`, `/api/deploy/`, `/api/history/`).
- `deploy/templates/deploy/*.html` – Legacy form UI plus blockchain dashboard rendered directly by Django.
- `deploy/management/commands/*.py` – Operational utilities (e.g., `clear_blocks.py`, `rotate_blocks.py`) for resetting or maintaining the ledger.
- `deployments/` – Re-created at runtime; stores generated site assets plus `.deployment_info` metadata. The repo keeps the folder (via `.gitkeep`) but not the generated deploy-* directories.
- `requirements.txt`, `setup.sh`, `docker-compose.yml` – Dependency list and helper scripts to reproduce the backend environment.

### Pipeline Contribution
1. `POST /api/deploy/` hits `deploy/api_views.py::deploy_repository`.
2. `deploy/services.py` verifies the repo, gathers diffs, and invokes `ai_code_validator()`.
3. The agents respond with a verdict/consensus score; Django stores it on a `Block` row and, if approved, spins up a static server under `deployments/`.
4. The API responds with deployment metadata that the React app displays.

## Frontend (`deployment-platform/deployment-dashboard`)

### Purpose
Provides the authenticated UX for repo submission, blockchain monitoring, and deployment management. Built with React, Vite, Tailwind, and shadcn-ui components.

### Main Components
- `src/services/blockchainApi.ts` – Centralized fetch wrapper for every Django endpoint (status, validate, deploy, history). Handles logging and polling semantics for live monitoring.
- `src/components/StarfallApp.tsx` – Landing form + validation workflow; submits GitHub URLs, triggers agent validation, and shows consensus explanations.
- `src/pages/DeploymentManager.tsx` – Management dashboard that merges backend history with local state, allows repo reconfiguration, and links to live deployment URLs.
- `src/components/ValidationResults.tsx` & `BlockIdDisplay.tsx` – Visualization of blockchain metadata (agent counts, block hash, etc.).
- `tailwind.config.ts`, `postcss.config.js`, `vite.config.ts` – Build tooling and design system configuration.

### Pipeline Contribution
1. The React app calls `blockchainApi.validateRepository()` for quick feedback.
2. On deploy, it calls `blockchainApi.deployRepository()` which forwards to Django’s `/api/deploy/` endpoint.
3. Polling (`startBlockchainMonitoring`) keeps the UI in sync with the blockchain state returned by `/api/status/`.
4. Deployment history queries populate `DeploymentManager`, while repo updates call `deployRepository` again to redeploy via the backend.

## How Backend and Frontend Interact

- **API Contract**: JSON request/response payloads defined in `src/services/blockchainApi.ts` mirror `backend/deploy/api_views.py` serializers.
- **Ports**: Backend typically runs on `http://127.0.0.1:8000`, while Vite runs on `http://127.0.0.1:5173` (adjust via `.env` / config). CORS is enabled in Django settings for local development.
- **Agents Dependency**: When Django handles `/api/deploy/`, it loads the sibling `agents/` package (via relative `Path` logic inside `deploy/services.py`). Make sure the Python environment can import that folder or run both projects inside the same repo checkout.

Use this README to orient new contributors; detailed setup guides still live in `deployment-platform/backend/DJANGO_README.md` and the frontend's `README.md`.
