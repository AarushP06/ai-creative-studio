"""Checks your setup before class.   python scripts/check_setup.py

Never prints your API key — only whether one is present.
"""
from __future__ import annotations

import importlib
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OK, WARN, FAIL = "  OK  ", " WARN ", " FAIL "
problems = 0


def report(status: str, message: str) -> None:
    global problems
    if status == FAIL:
        problems += 1
    print(f"[{status}] {message}")


# 1. Python version
v = sys.version_info
report(OK if v >= (3, 11) else FAIL, f"Python {v.major}.{v.minor}.{v.micro} (need 3.11+)")

# 2. Virtual environment
in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
report(OK if in_venv else WARN, "virtual environment active" if in_venv else "no virtual environment active (.venv recommended)")

# 3. Packages
for module in ("fastapi", "uvicorn", "pydantic", "google.genai", "mcp", "dotenv", "pytest"):
    try:
        importlib.import_module(module)
        report(OK, f"package {module}")
    except ImportError:
        report(FAIL, f"package {module} missing → pip install -r requirements.txt")

# 4. .env and the key (value never printed)
env = ROOT / ".env"
if env.exists():
    from dotenv import dotenv_values

    key = (dotenv_values(env).get("GEMINI_API_KEY") or "").strip()
    report(OK if key else WARN, "GEMINI_API_KEY present in .env" if key else "GEMINI_API_KEY empty → mock mode (that is fine for checkpoints 1–2)")
else:
    report(WARN, ".env not found → mock mode. Create it: copy .env.example .env")

# 5. Git ignores .env
try:
    out = subprocess.run(["git", "check-ignore", ".env"], cwd=ROOT, capture_output=True, text=True)
    report(OK if out.stdout.strip() == ".env" else FAIL, ".env is ignored by Git" if out.stdout.strip() == ".env" else ".env is NOT ignored by Git — fix .gitignore before committing")
except FileNotFoundError:
    report(WARN, "git not found on PATH")

# 6. Port 8000
port = int(os.getenv("PORT", "8000"))
with socket.socket() as s:
    busy = s.connect_ex(("127.0.0.1", port)) == 0
report(WARN if busy else OK, f"port {port} is busy — stop the other server or set PORT=8001" if busy else f"port {port} is free")

print("\nResult:", "READY" if problems == 0 else f"{problems} problem(s) to fix")
sys.exit(1 if problems else 0)
