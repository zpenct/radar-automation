"""Hermes cron entry point for Job Radar (``--no-agent`` mode).

Hermes treats the script's stdout as the message to deliver, an empty stdout as
"nothing to send", and a non-zero exit code as a failure. This wrapper only runs the
pipeline inside the project's virtual environment and forwards that contract.

``__PROJECT_DIR__`` is replaced with the repository path by ``install.ps1``.
"""
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(r"__PROJECT_DIR__")
VENV_PYTHON = ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"

result = subprocess.run(
    [str(PROJECT_DIR / VENV_PYTHON), "-X", "utf8", "-m", "radar", "run"],
    cwd=PROJECT_DIR,
    capture_output=True,
    text=True,
    encoding="utf-8",
    timeout=900,
)
sys.stdout.write(result.stdout)
if result.returncode != 0:
    sys.stderr.write(result.stderr[-1500:])
    sys.exit(result.returncode)
