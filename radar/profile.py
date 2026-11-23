"""Search profile loading.

Resolution order: ``RADAR_PROFILE`` environment variable, ``profile.yaml``,
then the bundled ``profile.example.yaml``.
"""
from pathlib import Path

import yaml

from radar import config


def load(path: str | Path | None = None) -> dict:
    candidates = [path, config.get("RADAR_PROFILE"), config.ROOT / "profile.yaml"]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return _read(Path(candidate))
    return _read(config.ROOT / "profile.example.yaml")


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))
