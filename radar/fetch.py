"""Fetch stage: pull postings from every source and store the new ones."""
import logging

from radar import db
from radar.sources import SOURCES

log = logging.getLogger(__name__)


def run() -> dict[str, int]:
    """Fetch all sources. Returns new-job counts per source (``-1`` on failure).

    A failing source is logged and skipped so it cannot block the others.
    """
    conn = db.connect()
    summary: dict[str, int] = {}
    for name, fetcher in SOURCES.items():
        try:
            fetched = fetcher()
        except Exception as exc:
            log.error("source=%s failed: %s", name, exc)
            summary[name] = -1
            continue
        inserted = db.add_new(conn, fetched)
        log.info("source=%s fetched=%d new=%d", name, len(fetched), len(inserted))
        summary[name] = len(inserted)
    return summary
