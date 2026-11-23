"""End-to-end run: fetch -> pre-filter -> score -> digest."""
from radar import db, digest, fetch, score


def run(
    do_fetch: bool = True,
    score_limit: int = 40,
    preview: bool = False,
    min_score: int | None = None,
) -> tuple[str, list]:
    """Run the pipeline and return ``(message, rows)``.

    ``rows`` are the jobs included in ``message``; the caller decides whether to
    deliver the message and mark the rows as sent.
    """
    if do_fetch:
        summary = fetch.run()
        if summary and all(count < 0 for count in summary.values()):
            raise RuntimeError("All job sources failed")
    score.run(limit=score_limit)

    conn = db.connect()
    rows = digest.pick(conn, min_score=min_score, include_sent=preview)
    return digest.format_digest(rows, preview=preview), rows
