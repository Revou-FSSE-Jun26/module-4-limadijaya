"""Measures read latency of a running RevoTask API (NFR-005).

Usage: python scripts/measure_latency.py https://your-api.example [requests_per_endpoint]
One warm-up request per endpoint, then N sequential requests (default 100). Prints p50, p95, max in ms.
It creates one throwaway user and a small board (3 columns, 6 cards) and deletes the board at the end.
The numbers include the network path from the machine that runs the script.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1].rstrip("/")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 100


def call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json"}
    if data:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read() or b"null")["data"]


email = f"latency-{int(time.time())}@example.com"
call("POST", "/api/auth/register", {"name": "Latency", "email": email, "password": "Latency-pass-1"})
token = call("POST", "/api/auth/login", {"email": email, "password": "Latency-pass-1"})["access_token"]
board = call("POST", "/api/boards", {"name": "Latency board"}, token)
for name in ("To do", "Doing", "Done"):
    column = call("POST", f"/api/boards/{board['id']}/columns", {"name": name}, token)
    for i in range(2):
        call("POST", f"/api/columns/{column['id']}/cards", {"title": f"{name} {i}"}, token)

endpoints = [
    "/api/health",
    "/api/boards",
    f"/api/boards/{board['id']}",
    f"/api/boards/{board['id']}/analytics",
    "/api/cards?assignee=me",
    "/api/notifications",
    "/api/users/me",
]
print(f"{'endpoint':42} {'p50':>7} {'p95':>7} {'max':>7}  (ms, n={N}, after 1 warm-up)")
for path in endpoints:
    call("GET", path, token=token)
    samples = []
    for _ in range(N):
        start = time.perf_counter()
        call("GET", path, token=token)
        samples.append((time.perf_counter() - start) * 1000)
    samples.sort()
    p95 = samples[max(0, int(round(0.95 * N)) - 1)]
    label = path.replace(board["id"], "{id}")
    print(f"{label:42} {statistics.median(samples):7.0f} {p95:7.0f} {samples[-1]:7.0f}")
call("DELETE", f"/api/boards/{board['id']}", token=token)
print(f"Dataset: 1 board, 3 columns, 6 cards. User {email} remains and can be deleted.")
