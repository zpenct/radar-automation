"""Digest assembly: select high-scoring jobs and render them as plain text."""
from datetime import date

from radar import db, profile

MAX_ITEMS = 8
DEFAULT_MIN_SCORE = 60
SOURCE_NAMES = {"remotive": "Remotive", "remoteok": "Remote OK", "wwr": "We Work Remotely"}


def pick(conn, min_score: int | None = None, limit: int = MAX_ITEMS, include_sent: bool = False):
    if min_score is None:
        preferences = profile.load().get("preferences", {})
        min_score = preferences.get("min_score", DEFAULT_MIN_SCORE)
    return db.top_scored(conn, min_score, limit, include_sent)


def format_digest(rows, preview: bool = False) -> str:
    """Render rows as a plain-text message; returns an empty string when there are none."""
    if not rows:
        return ""
    today = date.today().isoformat()
    if preview:
        lines = [
            f"Job Radar - preview {today}",
            f"Top {len(rows)} scored jobs (including already sent):",
            "",
        ]
    else:
        lines = [f"Job Radar - {today}", f"{len(rows)} new matching job(s):", ""]
    for index, row in enumerate(rows, 1):
        lines.append(f"{index}. {row['title']} - {row['company']} ({row['score']}/100)")
        if row["reason"]:
            lines.append(f"   {row['reason']}")
        meta = [f"Location: {row['location'] or '-'}"]
        if row["salary"]:
            meta.append(f"Salary: {row['salary']}")
        meta.append(f"Source: {SOURCE_NAMES.get(row['source'], row['source'])}")
        lines.append("   " + " | ".join(meta))
        lines.append(f"   {row['url']}")
        lines.append("")
    return "\n".join(lines).rstrip()
