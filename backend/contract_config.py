"""Web3 contract config.

IMPORTANT:
- After deploying `blockchain/FileAccess.sol` to your Ganache instance, update
  CONTRACT_ADDRESS below to the deployed contract address.
"""

# Replace this with your deployed address (Ganache changes addresses if you restart or redeploy).
CONTRACT_ADDRESS = "0xa6e964B3e4251C698d45f32C33746AD618aC183A"
# ABI for `blockchain/FileAccess.sol` (converted to Python literals)
ABI =[
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "fileId",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "owner",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "user",
        "type": "address"
      }
    ],
    "name": "AccessGranted",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "fileId",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "requester",
        "type": "address"
      }
    ],
    "name": "AccessRequested",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "fileId",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "owner",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "string",
        "name": "ipfsHash",
        "type": "string"
      }
    ],
    "name": "FileStored",
    "type": "event"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "fileId",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "user",
        "type": "address"
      }
    ],
    "name": "grantAccess",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "fileId",
        "type": "uint256"
      }
    ],
    "name": "requestAccess",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "string",
        "name": "ipfsHash",
        "type": "string"
      }
    ],
    "name": "storeFile",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "name": "accessRequests",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "fileCount",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "name": "files",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "id",
        "type": "uint256"
      },
      {
        "internalType": "string",
        "name": "ipfsHash",
        "type": "string"
      },
      {
        "internalType": "address",
        "name": "owner",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "fileId",
        "type": "uint256"
      }
    ],
    "name": "getAccessRequests",
    "outputs": [
      {
        "internalType": "address[]",
        "name": "",
        "type": "address[]"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "fileId",
        "type": "uint256"
      }
    ],
    "name": "getFile",
    "outputs": [
      {
        "internalType": "string",
        "name": "",
        "type": "string"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "fileId",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "user",
        "type": "address"
      }
    ],
    "name": "hasAccess",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "name": "permissions",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
]