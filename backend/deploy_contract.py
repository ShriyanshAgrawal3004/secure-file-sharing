"""Deploy FileAccess.sol to Ganache and update contract_config.py.

Usage:
  python deploy_contract.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from solcx import compile_source, install_solc
from web3 import Web3

BASE_DIR = Path(__file__).resolve().parent
CONTRACT_PATH = BASE_DIR.parent / "blockchain" / "FileAccess.sol"
CONFIG_PATH = BASE_DIR / "contract_config.py"
GANACHE_URL = os.environ.get("GANACHE_URL", "http://127.0.0.1:7545")
SOLC_VERSION = os.environ.get("SOLC_VERSION", "0.8.20")
EVM_VERSION = os.environ.get("EVM_VERSION", "paris")


def _compile_contract() -> tuple[list[dict], str]:
    with CONTRACT_PATH.open("r", encoding="utf-8") as f:
        source = f.read()

    install_solc(SOLC_VERSION)
    compiled = compile_source(source, solc_version=SOLC_VERSION, evm_version=EVM_VERSION)
    _, contract_interface = compiled.popitem()
    return contract_interface["abi"], contract_interface["bin"]


def _deploy(abi: list[dict], bytecode: str) -> str:
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    if not w3.is_connected():
        raise RuntimeError(f"Ganache not connected at {GANACHE_URL}")

    account = w3.eth.accounts[0]
    w3.eth.default_account = account
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    tx_hash = contract.constructor().transact(
        {
            "from": account,
            "gas": 3_000_000,
            "gasPrice": w3.to_wei("2", "gwei"),
        }
    )
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.contractAddress


def _update_config(new_address: str) -> None:
    content = CONFIG_PATH.read_text(encoding="utf-8")
    marker = "CONTRACT_ADDRESS = "
    if marker not in content:
        raise RuntimeError("Could not find CONTRACT_ADDRESS in contract_config.py")

    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(marker):
            lines[i] = f"{marker}\"{new_address}\""
            break
    else:
        raise RuntimeError("Could not update CONTRACT_ADDRESS in contract_config.py")

    CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    abi, bytecode = _compile_contract()
    address = _deploy(abi, bytecode)
    _update_config(address)
    print(json.dumps({"contract_address": address, "ganache_url": GANACHE_URL}, indent=2))


if __name__ == "__main__":
    main()
