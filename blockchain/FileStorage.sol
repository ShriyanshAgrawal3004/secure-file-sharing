// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FileStorage {

    enum Role { NONE, VIEWER, ADMIN }

    struct File {
        string ipfsHash;
        address owner;
    }

    uint public fileCount = 0;

    mapping(uint => File) public files;

    // fileId → user → role
    mapping(uint => mapping(address => Role)) public roles;

    // fileId → user → requested
    mapping(uint => mapping(address => bool)) public accessRequests;

    // 📤 Upload file
    function addFile(string memory _ipfsHash) public {
        fileCount++;

        files[fileCount] = File(_ipfsHash, msg.sender);

        // Owner = ADMIN
        roles[fileCount][msg.sender] = Role.ADMIN;
    }

    // 🙋 Request access
    function requestAccess(uint fileId) public {
        accessRequests[fileId][msg.sender] = true;
    }

    // ✅ Grant access
    function grantAccess(uint fileId, address user, Role role) public {
        require(msg.sender == files[fileId].owner, "Not owner");
        require(accessRequests[fileId][user], "No request");

        roles[fileId][user] = role;
        accessRequests[fileId][user] = false;
    }

    // ❌ Revoke access
    function revokeAccess(uint fileId, address user) public {
        require(msg.sender == files[fileId].owner, "Not owner");

        roles[fileId][user] = Role.NONE;
    }

    // 🔍 Check role
    function getRole(uint fileId, address user) public view returns (Role) {
        return roles[fileId][user];
    }

    // 📥 Get file (only authorized)
    function getFile(uint fileId) public view returns (string memory) {
        require(roles[fileId][msg.sender] != Role.NONE, "Access denied");

        return files[fileId].ipfsHash;
    }
}