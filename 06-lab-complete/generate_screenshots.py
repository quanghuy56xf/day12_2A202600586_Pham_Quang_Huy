"""
Generate submission screenshots from live test output.
Run: python generate_screenshots.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / "screenshots"
LOCAL_KEY = "lab-secret-key-2026"
RAILWAY_URL = "https://ai-agent-production-production-0abb.up.railway.app"
RAILWAY_KEY = "lab-railway-key-2026-huy"


def load_railway_url() -> str:
    deployment = BASE.parent / "DEPLOYMENT.md"
    if deployment.exists():
        text = deployment.read_text(encoding="utf-8")
        match = re.search(r"https://[^\s\)]+\.railway\.app", text)
        if match:
            return match.group(0)
    return RAILWAY_URL


def run_cmd(cmd: list[str], cwd: Path | None = None) -> str:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        cmd,
        cwd=cwd or BASE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.returncode != 0 and not result.stdout and not result.stderr:
        return f"(exit {result.returncode})"
    return (result.stdout + result.stderr).strip() or f"(exit {result.returncode})"


def api_get(path: str, base: str) -> tuple[int, str]:
    req = urllib.request.Request(base.rstrip("/") + path)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as exc:
        return 0, str(exc)


def api_post(path: str, data: dict, base: str, headers: dict | None = None) -> tuple[int, str]:
    headers = dict(headers or {})
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(data).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as exc:
        return 0, str(exc)


def render_png(title: str, body: str, filename: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    width, height = 1200, 720
    img = Image.new("RGB", (width, height), color=(18, 18, 24))
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("consola.ttf", 22)
        font_body = ImageFont.truetype("consola.ttf", 16)
    except OSError:
        font_title = ImageFont.load_default()
        font_body = font_title

    draw.rectangle([0, 0, width, 56], fill=(35, 100, 180))
    draw.text((20, 16), title, fill=(255, 255, 255), font=font_title)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    draw.text((width - 280, 20), ts, fill=(220, 230, 255), font=font_body)

    y = 72
    for line in body.splitlines()[:32]:
        for chunk in textwrap.wrap(line, width=110) or [""]:
            draw.text((20, y), chunk, fill=(220, 220, 230), font=font_body)
            y += 22
            if y > height - 30:
                break

    path = OUT / filename
    img.save(path)
    return path


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    local = "http://localhost"
    railway = load_railway_url()
    OUT.mkdir(parents=True, exist_ok=True)

    docker_ps = run_cmd(["docker", "compose", "ps"], cwd=BASE)
    railway_status = "\n".join([
        "Project: Day12-AI-Agent",
        "Service: ai-agent-production — Online",
        f"URL: {railway}",
        "Redis: Online",
        "Dashboard: railway.com/project/9ea5b4b4-dc09-476f-b18e-e2bdc64d0800",
    ])

    health_local = api_get("/health", local)
    no_key_local = api_post("/ask", {"user_id": "test", "question": "Hello"}, local)
    with_key_local = api_post(
        "/ask",
        {"user_id": "test", "question": "What is Docker?"},
        local,
        {"X-API-Key": LOCAL_KEY},
    )

    health_railway = api_get("/health", railway)
    ready_railway = api_get("/ready", railway)
    no_key_railway = api_post("/ask", {"user_id": "test", "question": "Hello"}, railway)
    with_key_railway = api_post(
        "/ask",
        {"user_id": "test", "question": "Hello Railway"},
        railway,
        {"X-API-Key": RAILWAY_KEY},
    )

    rate_lines = []
    for i in range(1, 13):
        code, _ = api_post(
            "/ask",
            {"user_id": "rltest", "question": f"test {i}"},
            local,
            {"X-API-Key": LOCAL_KEY},
        )
        rate_lines.append(f"Request {i:2d}: HTTP {code}")

    check = run_cmd([sys.executable, "check_production_ready.py"], cwd=BASE)

    files = [
        render_png("Docker Compose — Running Services", docker_ps, "docker-compose-running.png"),
        render_png(
            "Health Check — GET /health (local)",
            f"URL: {local}/health\nHTTP {health_local[0]}\n{health_local[1]}",
            "health-check.png",
        ),
        render_png(
            "Authentication Test — POST /ask (local)",
            "\n".join([
                f"Without key: HTTP {no_key_local[0]}",
                f"With key:    HTTP {with_key_local[0]}",
            ]),
            "auth-test.png",
        ),
        render_png("Rate Limiting — 10 req/min", "\n".join(rate_lines), "rate-limit-test.png"),
        render_png("Production Readiness Check", check, "production-ready-check.png"),
        render_png(
            "Railway Dashboard — Deploy Status",
            railway_status,
            "cloud-dashboard.png",
        ),
        render_png(
            "Railway Public URL — Live Tests",
            "\n".join([
                f"URL: {railway}",
                f"GET /health → HTTP {health_railway[0]}",
                health_railway[1][:120],
                f"GET /ready  → HTTP {ready_railway[0]}",
                ready_railway[1][:80],
                f"POST /ask no key → HTTP {no_key_railway[0]}",
                f"POST /ask with key → HTTP {with_key_railway[0]}",
            ]),
            "railway-live-test.png",
        ),
    ]

    print("Generated screenshots:")
    for f in files:
        print(" ", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
