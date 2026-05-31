from web3 import Web3

ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

if web3.is_connected():
    print("Connected to Blockchain!")
    print(web3.eth.accounts)
else:
    print("Connection Failed")
