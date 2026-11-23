from radar import db


def test_add_new_deduplicates_by_source_and_id(conn, make_job):
    first = db.add_new(conn, [make_job(), make_job(external_id="2")])
    again = db.add_new(conn, [make_job(), make_job(external_id="3")])
    assert len(first) == 2
    assert [job["external_id"] for job in again] == ["3"]
    assert len(db.all_jobs(conn)) == 3


def test_same_id_from_different_sources_is_distinct(conn, make_job):
    inserted = db.add_new(conn, [make_job(source="a"), make_job(source="b")])
    assert len(inserted) == 2


def test_unscored_excludes_scored_jobs(conn, make_job):
    db.add_new(conn, [make_job(), make_job(external_id="2")])
    db.save_score(conn, make_job(), 80, "good fit")
    assert [row["external_id"] for row in db.unscored(conn)] == ["2"]


def test_top_scored_respects_threshold_ordering_and_sent_flag(conn, make_job):
    db.add_new(conn, [make_job(external_id=str(i)) for i in range(1, 5)])
    for ident, score in {"1": 90, "2": 70, "3": 40, "4": 85}.items():
        db.save_score(conn, make_job(external_id=ident), score, "")

    rows = db.top_scored(conn, min_score=60, limit=10)
    assert [row["external_id"] for row in rows] == ["1", "4", "2"]

    db.mark_sent(conn, rows[:1])
    pending = db.top_scored(conn, min_score=60, limit=10)
    assert [row["external_id"] for row in pending] == ["4", "2"]

    with_sent = db.top_scored(conn, min_score=60, limit=10, include_sent=True)
    assert [row["external_id"] for row in with_sent] == ["1", "4", "2"]
