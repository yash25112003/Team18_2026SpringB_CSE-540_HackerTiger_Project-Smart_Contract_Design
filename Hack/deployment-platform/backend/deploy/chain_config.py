import json
import os
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_deployment_record() -> dict:
    deployment_file = _repo_root() / "deployed-address.json"
    if not deployment_file.exists():
        return {}

    try:
        return json.loads(deployment_file.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def get_chain_config() -> dict:
    deployment_record = _load_deployment_record()
    contract_address = os.environ.get("DEPLOYMENT_VALIDATOR_ADDRESS") or deployment_record.get("address", "")
    rpc_url = os.environ.get("SEPOLIA_RPC_URL", "")

    return {
        "network": os.environ.get("BLOCKCHAIN_NETWORK", deployment_record.get("network", "sepolia")),
        "contract_name": deployment_record.get("contractName", "DeploymentValidationLedger"),
        "contract_address": contract_address,
        "deployer": deployment_record.get("deployer", ""),
        "explorer_url": deployment_record.get(
            "explorerUrl",
            f"https://sepolia.etherscan.io/address/{contract_address}" if contract_address else "",
        ),
        "rpc_url_configured": bool(rpc_url),
        "deployment_metadata_found": bool(deployment_record),
    }
