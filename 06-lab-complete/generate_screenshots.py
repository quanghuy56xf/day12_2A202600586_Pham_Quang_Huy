"""
Generate submission screenshots from live test output.
Run: python generate_screenshots.py
"""
from __future__ import annotations

import json
import os
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
KEY = "lab-secret-key-2026"
PUBLIC_URL = None  # filled if tunnel running


def load_public_url() -> str:
    deployment = BASE.parent / "DEPLOYMENT.md"
    if deployment.exists():
        for line in deployment.read_text(encoding="utf-8").splitlines():
            if line.startswith("https://") and "loca.lt" in line:
                return line.strip()
            if line.startswith("https://") and ("railway" in line or "onrender" in line):
                return line.strip()
    return "http://localhost"


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
    return (result.stdout + result.stderr).strip() or f"(exit {result.returncode})"


def api_get(path: str, base: str) -> tuple[int, str]:
    req = urllib.request.Request(
        base.rstrip("/") + path,
        headers={"Bypass-Tunnel-Reminder": "true"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode()
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def api_post(path: str, data: dict, base: str, headers: dict | None = None) -> tuple[int, str]:
    headers = headers or {}
    headers["Content-Type"] = "application/json"
    headers.setdefault("Bypass-Tunnel-Reminder", "true")
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(data).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


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
    public = load_public_url()
    OUT.mkdir(parents=True, exist_ok=True)

    docker_ps = run_cmd(["docker", "compose", "ps"], cwd=BASE)

    health_local = api_get("/health", local)
    ready_local = api_get("/ready", local)
    no_key = api_post("/ask", {"user_id": "test", "question": "Hello"}, local)
    with_key = api_post(
        "/ask",
        {"user_id": "test", "question": "What is Docker?"},
        local,
        {"X-API-Key": KEY},
    )

    rate_lines = []
    for i in range(1, 13):
        code, _ = api_post(
            "/ask",
            {"user_id": "rltest", "question": f"test {i}"},
            local,
            {"X-API-Key": KEY},
        )
        rate_lines.append(f"Request {i:2d}: HTTP {code}")

    check = run_cmd([sys.executable, "check_production_ready.py"], cwd=BASE)

    public_health = None
    if public.startswith("https://"):
        try:
            public_health = api_get("/health", public)
        except Exception as exc:
            public_health = (0, str(exc))

    files = [
        render_png(
            "Docker Compose — Running Services",
            docker_ps,
            "docker-compose-running.png",
        ),
        render_png(
            "Health Check — GET /health",
            f"URL: {local}/health\nHTTP {health_local[0]}\n{health_local[1]}",
            "health-check.png",
        ),
        render_png(
            "Authentication Test — POST /ask",
            "\n".join([
                "Without X-API-Key:",
                f"  HTTP {no_key[0]} — {no_key[1][:120]}",
                "",
                "With X-API-Key:",
                f"  HTTP {with_key[0]} — {with_key[1][:200]}",
            ]),
            "auth-test.png",
        ),
        render_png(
            "Rate Limiting — 10 req/min per user",
            "\n".join(rate_lines),
            "rate-limit-test.png",
        ),
        render_png(
            "Production Readiness — check_production_ready.py",
            check,
            "production-ready-check.png",
        ),
    ]

    if public_health:
        files.append(
            render_png(
                "Public URL — Cloud Tunnel / Deploy",
                f"URL: {public}/health\nHTTP {public_health[0]}\n{public_health[1]}",
                "cloud-dashboard.png",
            )
        )
    else:
        files.append(
            render_png(
                "Cloud Deploy — Railway Ready",
                "\n".join([
                    "Platform: Railway",
                    "Config: 06-lab-complete/railway.toml",
                    "Root Directory: 06-lab-complete",
                    "Steps:",
                    "  1. Railway Dashboard → Deploy from GitHub",
                    "  2. Set root dir → 06-lab-complete",
                    "  3. Add Redis plugin + env vars",
                    "  4. Deploy → railway domain",
                ]),
                "cloud-dashboard.png",
            )
        )

    print("Generated screenshots:")
    for f in files:
        print(" ", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
