import pytest
import requests

from radar import telegram


def test_split_message_keeps_short_text_whole():
    assert telegram.split_message("one\n\ntwo") == ["one\n\ntwo"]


def test_split_message_respects_the_size_limit():
    block = "x" * 1500
    chunks = telegram.split_message("\n\n".join([block] * 5))
    assert len(chunks) > 1
    assert all(len(chunk) <= telegram.MAX_MESSAGE_LENGTH for chunk in chunks)


def test_send_posts_each_chunk(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    calls = []

    class Ok:
        ok = True

    monkeypatch.setattr(
        telegram.requests, "post", lambda url, json, timeout: calls.append((url, json)) or Ok()
    )
    assert telegram.send("hello") == 1
    assert calls[0][1] == {"chat_id": "42", "text": "hello", "disable_web_page_preview": True}


def test_network_errors_never_leak_the_bot_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:secret-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")

    def boom(url, json, timeout):
        raise requests.ConnectionError(f"failed to reach {url}")

    monkeypatch.setattr(telegram.requests, "post", boom)
    with pytest.raises(RuntimeError) as excinfo:
        telegram.send("hello")
    assert "secret-token" not in str(excinfo.value)
    assert excinfo.value.__cause__ is None


def test_api_rejection_surfaces_status_and_description(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")

    class Rejected:
        ok = False
        status_code = 400

        def json(self):
            return {"description": "chat not found"}

    monkeypatch.setattr(telegram.requests, "post", lambda *a, **k: Rejected())
    with pytest.raises(RuntimeError, match="400 chat not found"):
        telegram.send("hello")
