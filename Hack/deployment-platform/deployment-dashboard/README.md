# Starfall Evolve Frontend

React + Vite UI for the blockchain-governed deployment platform. It talks directly to the Django backend under `deployment-platform/backend/` and renders validation, blockchain, and deployment details for users.

## Purpose in the Pipeline

1. Collect GitHub repository URLs (and optional commit hashes).
2. Call Django’s `/api/validate/` and `/api/deploy/` endpoints via the `blockchainApi` helper.
3. Visualize agent verdicts, consensus scores, and block IDs returned by the backend.
4. Provide a management console for previously deployed repos, including redeploy + delete actions.

## Key Modules

- `src/services/blockchainApi.ts` – Strongly typed API client wrapping `fetch`. Handles polling, logging, and serialization of Django responses. Update this file whenever backend contracts change.
- `src/components/StarfallApp.tsx` – Landing workflow: repo form, validation toast pipeline, and agent result cards.
- `src/pages/DeploymentManager.tsx` – Grid view of every deployment (merged from backend history + localStorage to remain responsive). Supports editing repo URLs and links to live deployments via `getDisplayUrl()`.
- `src/components/ValidationResults.tsx` – Detailed agent/consensus visualizations fed by the `validation` payload from `/api/deploy/`.
- `src/components/BlockIdDisplay.tsx` – UI component that surfaces active block metadata and status badges.
- `src/components/DeploymentManager.tsx` *(component wrapper)* – Lightweight adapter that allows the page component to be embedded elsewhere if needed.
- `tailwind.config.ts`, `postcss.config.js`, `tsconfig*.json`, `vite.config.ts` – Build + styling toolchain; adjust here for new paths, aliases, or design tokens.

## Running Locally

```bash
cd deployment-platform/deployment-dashboard
npm install
npm run dev
```

The dev server defaults to `http://127.0.0.1:5173`. The app expects the Django backend to be running at `http://127.0.0.1:8000`; update `blockchainApi.baseUrl` if you expose it elsewhere.

## How It Uses Backend Data

- **Status Polling**: `blockchainApi.startBlockchainMonitoring()` hits `/api/status/` every 15 seconds, broadcasting updates to dashboard components.
- **Repository Validation**: `validateRepository()` posts to `/api/validate/` for quick preflight checks before allowing the deploy CTA.
- **Deployments**: `deployRepository()` sends repo data to `/api/deploy/`, then the returned `deployment_url`, `block_hash`, and AI/static evidence populate the results cards.
- **History & Details**: `getDeploymentHistory()` hydrates `DeploymentManager` with canonical records; localStorage entries are normalized to backend schema to keep the UI responsive even before the HTTP call returns.

## Customization Tips

- Use `@/hooks/use-toast` for consistent alerts when surfacing backend errors or agent verdict details.
- When adding new API endpoints, extend `blockchainApi.ts` first, then pull the typed helper into the relevant component. This keeps all fetch/poll logic centralized.
- Tailwind tokens for gradients, glows, and badges live inside `tailwind.config.ts`; reuse them for new components to maintain the neon theme.

This README should give frontend contributors enough context to understand how their changes affect the overall deployment pipeline. For deeper backend details, see `../hackathon/README.md` and the repo root docs.
