# Sepolia Deployment Runbook

This runbook is the canonical demo path for Hacker Tiger. Follow it in order.

## 1. Configure Ethereum credentials

Create a root `.env` from the example:

```bash
cp .env.example .env
```

Set:

- `SEPOLIA_RPC_URL` to your Alchemy or Infura Sepolia HTTPS endpoint
- `ETH_PRIVATE_KEY` to a throwaway MetaMask wallet private key funded with Sepolia ETH

## 2. Install root smart-contract dependencies

```bash
npm install
```

## 3. Verify the contract locally

```bash
npx hardhat compile
npm test
```

The contract package is not ready for Sepolia until both commands pass.

## 4. Deploy to Sepolia

```bash
npm run deploy:sepolia
```

Expected outputs:

- deployer wallet address
- deployed `DeploymentValidationLedger` address
- Sepolia Etherscan URL
- generated `deployed-address.json` file at the repo root

## 5. Configure the Django backend

```bash
cp Hack/deployment-platform/backend/.env.example Hack/deployment-platform/backend/.env
```

Set:

- `GEMINI_API_KEYS` or `GEMINI_API_KEY`
- `SEPOLIA_RPC_URL`
- `DEPLOYMENT_VALIDATOR_ADDRESS`

You can copy the deployed address from the deploy script output or `deployed-address.json`.

Install and start the backend:

```bash
cd Hack/deployment-platform/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

## 6. Configure the React dashboard

```bash
cp Hack/deployment-platform/deployment-dashboard/.env.example Hack/deployment-platform/deployment-dashboard/.env
```

Set:

- `VITE_API_BASE=http://127.0.0.1:8000/api`
- `VITE_SEPOLIA_RPC_URL`
- `VITE_CONTRACT_ADDRESS`

Then start the frontend:

```bash
cd Hack/deployment-platform/deployment-dashboard
npm install
npm run build
npm run dev
```

## 7. Demo verification

- Visit `http://127.0.0.1:5173`
- Submit a GitHub repository URL
- Confirm Django `/api/status/` returns `chain_config` with the deployed contract address
- Confirm the deploy script output or `deployed-address.json` matches the backend/frontend configuration
- Open the Sepolia Etherscan link and confirm the contract is live
