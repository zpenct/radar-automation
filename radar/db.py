"""SQLite persistence.

A job is identified by ``(source, external_id)``; inserts use ``INSERT OR IGNORE``
so a posting is stored, scored, and delivered at most once.
"""
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from radar import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    source       TEXT NOT NULL,
    external_id  TEXT NOT NULL,
    title        TEXT,
    company      TEXT,
    location     TEXT,
    url          TEXT,
    tags         TEXT,
    salary       TEXT,
    posted_at    TEXT,
    description  TEXT,
    fetched_at   TEXT NOT NULL,
    score        INTEGER,
    reason       TEXT,
    status       TEXT NOT NULL DEFAULT 'new',
    PRIMARY KEY (source, external_id)
);
"""

STATUS_NEW, STATUS_SCORED, STATUS_SENT = "new", "scored", "sent"


def db_path() -> Path:
    override = config.get("RADAR_DB_PATH")
    return Path(override) if override else config.ROOT / "data" / "jobs.db"


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_new(conn: sqlite3.Connection, jobs: list[dict]) -> list[dict]:
    """Insert jobs and return only those that were not already stored."""
    now = datetime.now(UTC).isoformat()
    inserted = []
    for job in jobs:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO jobs
               (source, external_id, title, company, location, url, tags,
                salary, posted_at, description, fetched_at)
               VALUES (:source, :external_id, :title, :company, :location, :url,
                       :tags, :salary, :posted_at, :description, :fetched_at)""",
            {**job, "fetched_at": now},
        )
        if cursor.rowcount == 1:
            inserted.append(job)
    conn.commit()
    return inserted


def all_jobs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM jobs").fetchall()


def unscored(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM jobs WHERE score IS NULL").fetchall()


def save_score(conn: sqlite3.Connection, job, score: int, reason: str) -> None:
    conn.execute(
        "UPDATE jobs SET score=?, reason=?, status=? WHERE source=? AND external_id=?",
        (score, reason, STATUS_SCORED, job["source"], job["external_id"]),
    )
    conn.commit()


def top_scored(
    conn: sqlite3.Connection, min_score: int, limit: int, include_sent: bool = False
) -> list[sqlite3.Row]:
    statuses = (STATUS_SCORED, STATUS_SENT) if include_sent else (STATUS_SCORED,)
    placeholders = ",".join("?" for _ in statuses)
    return conn.execute(
        f"SELECT * FROM jobs WHERE status IN ({placeholders}) AND score >= ? "
        "ORDER BY score DESC LIMIT ?",
        (*statuses, min_score, limit),
    ).fetchall()


def mark_sent(conn: sqlite3.Connection, rows) -> None:
    conn.executemany(
        "UPDATE jobs SET status=? WHERE source=? AND external_id=?",
        [(STATUS_SENT, r["source"], r["external_id"]) for r in rows],
    )
    conn.commit()
