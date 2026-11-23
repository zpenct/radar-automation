"""Environment configuration helpers."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env(path: Path | None = None) -> None:
    """Load KEY=VALUE pairs from a .env file without overriding existing variables."""
    env_file = path or ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def get(name: str, default: str = "") -> str:
    """Return a setting from the environment (or .env), falling back to ``default``."""
    load_env()
    return os.environ.get(name, "").strip() or default


def require(name: str) -> str:
    """Return a required setting or exit with an actionable message."""
    value = get(name)
    if not value:
        raise SystemExit(f"Missing required setting: {name} (set it in .env)")
    return value
