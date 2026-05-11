from web3 import Web3
from contract_config import CONTRACT_ADDRESS, ABI

ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

contract = web3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=ABI
)

account = web3.eth.accounts[0]  # owner account
def store_file(ipfs_hash):
    tx = contract.functions.addFile(ipfs_hash).transact({
        'from': account
    })

    web3.eth.wait_for_transaction_receipt(tx)

    return tx.hex()
def grant_access(file_id, user_address):
    tx = contract.functions.grantAccess(file_id, user_address).transact({
        'from': account
    })
    web3.eth.wait_for_transaction_receipt(tx)