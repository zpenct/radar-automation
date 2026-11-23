import pytest

from radar import cli, db, pipeline, telegram


@pytest.fixture
def fake_pipeline(monkeypatch):
    state = {"message": "Digest text", "rows": [{"source": "s", "external_id": "1"}], "marked": []}
    monkeypatch.setattr(pipeline, "run", lambda **kwargs: (state["message"], state["rows"]))
    monkeypatch.setattr(db, "connect", lambda *args, **kwargs: object())
    monkeypatch.setattr(db, "mark_sent", lambda conn, rows: state["marked"].append(rows))
    return state


def test_run_prints_digest_to_stdout_only(fake_pipeline, capsys):
    assert cli.main(["run"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "Digest text\n"
    assert fake_pipeline["marked"] == [fake_pipeline["rows"]]


def test_run_is_silent_when_there_is_nothing_to_report(fake_pipeline, capsys):
    fake_pipeline["message"], fake_pipeline["rows"] = "", []
    assert cli.main(["run"]) == 0
    assert capsys.readouterr().out == ""
    assert fake_pipeline["marked"] == []


def test_dry_run_and_preview_do_not_mark_jobs_sent(fake_pipeline):
    cli.main(["run", "--dry-run"])
    cli.main(["run", "--preview"])
    assert fake_pipeline["marked"] == []


def test_send_delivers_via_telegram_instead_of_stdout(fake_pipeline, monkeypatch, capsys):
    sent = []
    monkeypatch.setattr(telegram, "send", lambda text: sent.append(text) or 1)
    cli.main(["run", "--send"])
    assert sent == ["Digest text"]
    assert capsys.readouterr().out == ""
    assert fake_pipeline["marked"] == [fake_pipeline["rows"]]
