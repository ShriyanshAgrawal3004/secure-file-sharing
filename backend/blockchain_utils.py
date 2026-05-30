from __future__ import annotations

from typing import Any, Dict

import os

from dotenv import load_dotenv
from web3 import Web3

from contract_config import ABI, CONTRACT_ADDRESS

load_dotenv()

GANACHE_URL = os.environ.get("GANACHE_URL", "http://127.0.0.1:7545")
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))


def _checksum(addr: str) -> str:
    if not addr:
        raise ValueError("Address is required")
    return Web3.to_checksum_address(addr)


def _contract():
    if not CONTRACT_ADDRESS or CONTRACT_ADDRESS == "0x0000000000000000000000000000000000000000":
        raise ValueError(
            "CONTRACT_ADDRESS not set. Deploy blockchain/FileAccess.sol and update backend/contract_config.py"
        )
    return web3.eth.contract(address=_checksum(CONTRACT_ADDRESS), abi=ABI)


def is_blockchain_ready() -> bool:
    try:
        return bool(web3.is_connected())
    except Exception:
        return False


def store_file(ipfs_hash: str, owner_address: str) -> Dict[str, Any]:
    """Store a file hash on-chain. Returns {tx_hash, file_id}."""
    if not ipfs_hash:
        raise ValueError("ipfs_hash is required")

    contract = _contract()
    owner = _checksum(owner_address)

    tx = contract.functions.storeFile(ipfs_hash).transact({"from": owner})
    web3.eth.wait_for_transaction_receipt(tx)

    file_id = contract.functions.fileCount().call()
    return {"tx_hash": tx.hex(), "file_id": int(file_id)}


def request_access(file_id: int, user_address: str) -> str:
    contract = _contract()
    user = _checksum(user_address)

    tx = contract.functions.requestAccess(int(file_id)).transact({"from": user})
    web3.eth.wait_for_transaction_receipt(tx)
    return tx.hex()


def grant_access(file_id: int, owner_address: str, user_address: str) -> str:
    contract = _contract()
    owner = _checksum(owner_address)
    user = _checksum(user_address)

    tx = contract.functions.grantAccess(int(file_id), user).transact({"from": owner})
    web3.eth.wait_for_transaction_receipt(tx)
    return tx.hex()


def revoke_access(file_id: int, owner_address: str, user_address: str) -> str:
    contract = _contract()
    owner = _checksum(owner_address)
    user = _checksum(user_address)

    if not hasattr(contract.functions, "revokeAccess"):
        raise ValueError("Active contract ABI does not expose revokeAccess")

    tx = contract.functions.revokeAccess(int(file_id), user).transact({"from": owner})
    web3.eth.wait_for_transaction_receipt(tx)
    return tx.hex()


def has_access(file_id: int, user_address: str) -> bool:
    contract = _contract()
    user = _checksum(user_address)
    return bool(contract.functions.hasAccess(int(file_id), user).call())


def get_file(file_id: int, user_address: str) -> str:
    """Return the IPFS hash if user is authorized (contract enforces this)."""
    contract = _contract()
    user = _checksum(user_address)
    return contract.functions.getFile(int(file_id)).call({"from": user})
