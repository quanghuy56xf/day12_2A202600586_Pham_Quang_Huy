import json
import sys
import urllib.request
import urllib.error

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://localhost"
KEY = "lab-secret-key-2026"


def post(path, data, headers=None):
    headers = headers or {}
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body


def get(path):
    with urllib.request.urlopen(BASE + path) as resp:
        return resp.status, json.loads(resp.read())


print("=== Health ===")
print(get("/health"))

print("\n=== Ready ===")
print(get("/ready"))

print("\n=== Ask without key (expect 401) ===")
print(post("/ask", {"user_id": "test", "question": "Hello"}))

print("\n=== Ask with key (expect 200) ===")
print(post("/ask", {"user_id": "test", "question": "What is Docker?"}, {"X-API-Key": KEY}))

print("\n=== Conversation history ===")
print(post("/ask", {"user_id": "alice", "question": "Hello"}, {"X-API-Key": KEY}))
print(post("/ask", {"user_id": "alice", "question": "Tell me more"}, {"X-API-Key": KEY}))

print("\n=== Rate limit (expect 429 after 10) ===")
for i in range(1, 13):
    code, _ = post("/ask", {"user_id": "rltest", "question": f"test {i}"}, {"X-API-Key": KEY})
    print(f"  Request {i}: HTTP {code}")
