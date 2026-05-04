# Hacker Tiger Smart Contract Design

## Project Overview
Hacker Tiger is a secure deployment assurance framework designed to improve auditability, transparency, and trust in software release pipelines. The broader system combines AI-based validation with blockchain-backed immutability to produce deployment decisions that are explainable, verifiable, and tamper-resistant.

This repository contains the **draft smart contract design** for the blockchain portion of the project.

## Purpose of the Smart Contract
The smart contract acts as the **on-chain audit and consensus layer** of Hacker Tiger.

It is responsible for:
- registering trusted validators
- creating deployment validation sessions
- recording validator votes
- storing hashes/URIs of off-chain evidence
- finalizing approval or rejection decisions
- emitting immutable audit events

## What Stays Off-Chain
The following components remain off-chain because they are computationally heavy or too large for practical on-chain storage:
- AI agent execution
- compliance and threat analysis
- repository cloning and deployment execution
- detailed reports and artifacts
- monitoring and health-check outputs

Instead of storing full reports on-chain, the contract stores **hashes and metadata references** so integrity can still be verified.

## Architecture Mapping
Hacker Tiger uses a layered architecture:
1. **Django Backend** – APIs, UI, orchestration, governance
2. **Multi-Agent Validation System** – AI-based analysis and consensus generation
3. **Deployment System** – secure execution and monitored deployment

The smart contract complements these layers by preserving a tamper-evident audit trail for validation sessions and consensus outcomes.

## Smart Contract Components
### `IValidationLedger.sol`
Defines:
- session data structures
- validator data structures
- events
- core function signatures

### `DeploymentValidationLedger.sol`
Implements:
- validator registration and removal
- session creation
- voting
- quorum-based finalization
- read functions for session and validator lookup

## Dependencies
- Node.js
- npm
- Hardhat
- Solidity `^0.8.20`
- Sepolia RPC endpoint and funded Sepolia wallet for live Ethereum deployment

## Setup Instructions
```bash
npm install
npx hardhat compile
npm test
```

## Sepolia Deployment

The contract package is configured for Sepolia through root environment variables:

- `SEPOLIA_RPC_URL`
- `ETH_PRIVATE_KEY`

Use the full deployment runbook in [SEPOLIA_DEPLOYMENT_RUNBOOK.md](/Users/ashishrajshekhar/Desktop/Team18_2026SpringB_CSE-540_HackerTiger_Project-Smart_Contract_Design/SEPOLIA_DEPLOYMENT_RUNBOOK.md). The deploy script writes `deployed-address.json`, which the Django backend can read as a fallback source of truth for the live contract address.
