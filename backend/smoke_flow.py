"""Minimal smoke test for the decentralized access-control flow.

This script assumes:
- Flask backend is running (default http://127.0.0.1:5000)
- Ganache is running and `backend/contract_config.py` has the deployed CONTRACT_ADDRESS

It uses HTTP requests to:
1) Upload a file as owner
2) Verify another user is denied
3) Request access as user2
4) Grant access as owner
5) Verify user2 can now retrieve the IPFS hash

Usage (from backend/):
    python3 smoke_flow.py --file ../frontend/index.html --owner 0x... --user 0x...
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Dict

import requests


def _json(resp: requests.Response) -> Dict[str, Any]:
    try:
        return resp.json()
    except Exception:
        return {"_raw": resp.text}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:5000")
    p.add_argument("--file", required=True)
    p.add_argument("--owner", required=True, help="Owner Ganache address")
    p.add_argument("--user", required=True, help="Requester Ganache address")
    p.add_argument("--sensitivity", type=int, default=5)
    args = p.parse_args()

    if not os.path.exists(args.file):
        raise SystemExit(f"File not found: {args.file}")

    # 1) upload
    with open(args.file, "rb") as f:
        files = {"file": (os.path.basename(args.file), f)}
        data = {
            "sensitivity": str(args.sensitivity),
            "owner_address": args.owner,
        }
        r = requests.post(f"{args.base}/upload", files=files, data=data, timeout=60)

    print("UPLOAD", r.status_code, _json(r))
    payload = _json(r)
    file_id = payload.get("file_id")
    if not file_id:
        raise SystemExit("Upload did not return file_id (check IPFS + contract deployment)")

    # 2) unauthorized get_file
    r = requests.get(f"{args.base}/get_file/{file_id}", params={"user_address": args.user}, timeout=30)
    print("GET (unauthorized)", r.status_code, _json(r))

    # 3) request access
    r = requests.post(
        f"{args.base}/request_access",
        json={"file_id": int(file_id), "user_address": args.user},
        timeout=30,
    )
    print("REQUEST", r.status_code, _json(r))

    # 4) grant
    r = requests.post(
        f"{args.base}/grant_access",
        json={"file_id": int(file_id), "owner_address": args.owner, "user_address": args.user},
        timeout=30,
    )
    print("GRANT", r.status_code, _json(r))

    # 5) authorized get_file
    r = requests.get(f"{args.base}/get_file/{file_id}", params={"user_address": args.user}, timeout=30)
    print("GET (authorized)", r.status_code, _json(r))


if __name__ == "__main__":
    main()
