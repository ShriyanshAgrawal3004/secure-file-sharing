// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FileStorage {

    struct File {
        string ipfsHash;
        address owner;
    }

    uint public fileCount = 0;

    mapping(uint => File) public files;

    // Access control: fileId → user → access
    mapping(uint => mapping(address => bool)) public access;

    // 📤 Add file
    function addFile(string memory _ipfsHash) public {
        fileCount++;
        files[fileCount] = File(_ipfsHash, msg.sender);

        // Owner has access by default
        access[fileCount][msg.sender] = true;
    }

    // 🔐 Grant access
    function grantAccess(uint fileId, address user) public {
        require(msg.sender == files[fileId].owner, "Not owner");
        access[fileId][user] = true;
    }

    // ❌ Revoke access
    function revokeAccess(uint fileId, address user) public {
        require(msg.sender == files[fileId].owner, "Not owner");
        access[fileId][user] = false;
    }

    // 🔍 Check access
    function hasAccess(uint fileId, address user) public view returns (bool) {
        return access[fileId][user];
    }

    // 📥 Get file hash (only if authorized)
    function getFile(uint fileId) public view returns (string memory) {
        require(access[fileId][msg.sender], "Access denied");
        return files[fileId].ipfsHash;
    }
}