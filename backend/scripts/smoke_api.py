"""Black-box smoke test of a running RevoTask API: one request per Blueprint, with status codes.

Usage:  python scripts/smoke_api.py https://your-api.example
Prints one line per call. Exits with 1 if any check fails. Use the output as the Postman/live-demo
evidence that all eight Blueprints are reachable. It creates one throwaway user and one board.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5055").rstrip("/")
failures = 0


def call(method: str, path: str, body=None, token: str | None = None, expect: int = 200):
    global failures
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status, payload = response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        status, payload = error.code, json.loads(error.read() or b"null")
    mark = "OK  " if status == expect else "FAIL"
    if status != expect:
        failures += 1
    print(f"{mark} {method:6} {path:48} -> {status} (expected {expect})")
    return payload


stamp = int(time.time())
email = f"smoke-{stamp}@example.com"
call("GET", "/api/health")
call("POST", "/api/auth/register", {"name": "Smoke Tester", "email": email, "password": "Smoke-pass-1"}, expect=201)
token = call("POST", "/api/auth/login", {"email": email, "password": "Smoke-pass-1"})["data"]["access_token"]
call("GET", "/api/users/me", token=token)
board = call("POST", "/api/boards", {"name": "Smoke board"}, token, expect=201)["data"]
call("GET", "/api/boards", token=token)
call("GET", f"/api/boards/{board['id']}", token=token)
todo = call("POST", f"/api/boards/{board['id']}/columns", {"name": "To do"}, token, expect=201)["data"]
done = call("POST", f"/api/boards/{board['id']}/columns", {"name": "Done"}, token, expect=201)["data"]
card = call("POST", f"/api/columns/{todo['id']}/cards", {"title": "Smoke card"}, token, expect=201)["data"]
call("PATCH", f"/api/cards/{card['id']}/position", {"column_id": done["id"], "order": 1024}, token)
comment = call("POST", f"/api/cards/{card['id']}/comments", {"content": "Smoke comment"}, token, expect=201)["data"]
call("GET", f"/api/cards/{card['id']}/comments", token=token)
call("PATCH", f"/api/comments/{comment['id']}", {"content": "Edited"}, token)
call("GET", "/api/cards?assignee=me", token=token)
call("GET", "/api/notifications", token=token)
call("GET", f"/api/boards/{board['id']}/analytics", token=token)
call("GET", "/api/boards", expect=401)
call("DELETE", f"/api/boards/{board['id']}", token=token)
print("\nAll checks passed." if failures == 0 else f"\n{failures} check(s) failed.")
sys.exit(1 if failures else 0)