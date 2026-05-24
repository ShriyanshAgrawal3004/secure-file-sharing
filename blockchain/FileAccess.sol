// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title FileAccess - Simple decentralized access control for IPFS-hosted encrypted files
/// @notice Stores only IPFS hashes on-chain. Encryption stays off-chain.
contract FileAccess {
    struct FileData {
        uint256 id;
        string ipfsHash;
        address owner;
    }

    uint256 public fileCount;

    mapping(uint256 => FileData) public files;
    mapping(uint256 => mapping(address => bool)) public permissions;
    mapping(uint256 => address[]) public accessRequests;

    event FileStored(uint256 indexed fileId, address indexed owner, string ipfsHash);
    event AccessRequested(uint256 indexed fileId, address indexed requester);
    event AccessGranted(uint256 indexed fileId, address indexed owner, address indexed user);

    /// @notice Store a new file IPFS hash
    function storeFile(string memory ipfsHash) public {
        require(bytes(ipfsHash).length > 0, "Empty IPFS hash");

        fileCount += 1;
        uint256 fileId = fileCount;

        files[fileId] = FileData({id: fileId, ipfsHash: ipfsHash, owner: msg.sender});

        emit FileStored(fileId, msg.sender, ipfsHash);
    }

    /// @notice Request access to a file. Prevents duplicate requests.
    function requestAccess(uint256 fileId) public {
        require(fileId > 0 && fileId <= fileCount, "Invalid fileId");
        require(msg.sender != files[fileId].owner, "Owner has access");

        // Prevent duplicate requests
        address[] storage reqs = accessRequests[fileId];
        for (uint256 i = 0; i < reqs.length; i++) {
            require(reqs[i] != msg.sender, "Already requested");
        }

        reqs.push(msg.sender);
        emit AccessRequested(fileId, msg.sender);
    }

    /// @notice Owner grants access to a user
    function grantAccess(uint256 fileId, address user) public {
        require(fileId > 0 && fileId <= fileCount, "Invalid fileId");
        require(msg.sender == files[fileId].owner, "Only owner");
        require(user != address(0), "Invalid user");

        permissions[fileId][user] = true;
        emit AccessGranted(fileId, msg.sender, user);
    }

    /// @notice Check whether a user has access: owner OR granted permission
    function hasAccess(uint256 fileId, address user) public view returns (bool) {
        require(fileId > 0 && fileId <= fileCount, "Invalid fileId");
        if (user == files[fileId].owner) {
            return true;
        }
        return permissions[fileId][user];
    }

    /// @notice Get the IPFS hash if caller is authorized
    function getFile(uint256 fileId) public view returns (string memory) {
        require(fileId > 0 && fileId <= fileCount, "Invalid fileId");
        require(hasAccess(fileId, msg.sender), "Access denied");
        return files[fileId].ipfsHash;
    }

    /// @notice Helper to return pending access requests list
    function getAccessRequests(uint256 fileId) public view returns (address[] memory) {
        require(fileId > 0 && fileId <= fileCount, "Invalid fileId");
        return accessRequests[fileId];
    }
}
