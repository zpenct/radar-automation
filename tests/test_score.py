import json

import pytest

from radar import score


def _completion(content: str, total_tokens: int = 42) -> str:
    return json.dumps(
        {"choices": [{"message": {"content": content}}], "usage": {"total_tokens": total_tokens}}
    )


def _sse(*pieces: str) -> str:
    chunks = [
        "data: " + json.dumps({"choices": [{"delta": {"content": piece}}]}) for piece in pieces
    ]
    usage = "data: " + json.dumps({"choices": [{"delta": {}}], "usage": {"total_tokens": 7}})
    return "\n\n".join([*chunks, usage, "data: [DONE]"])


def test_extract_text_from_json_body():
    assert score.extract_text(_completion("hello")) == "hello"


def test_extract_text_from_sse_stream():
    assert score.extract_text(_sse("Hel", "lo")) == "Hello"


def test_extract_usage_from_both_shapes():
    assert score.extract_usage(_completion("x", 42)) == 42
    assert score.extract_usage(_sse("x")) == 7
    assert score.extract_usage("not json") == 0


def test_parse_result_extracts_json_from_surrounding_text():
    text = 'Sure!\n```json\n{"score": 82, "reason": "Good fit."}\n```'
    assert score.parse_result(text) == {"score": 82, "reason": "Good fit."}


@pytest.mark.parametrize(("raw", "expected"), [(150, 100), (-5, 0)])
def test_parse_result_clamps_score(raw, expected):
    assert score.parse_result(json.dumps({"score": raw, "reason": ""}))["score"] == expected


def test_parse_result_rejects_replies_without_json():
    with pytest.raises(ValueError):
        score.parse_result("I cannot help with that.")


def test_build_prompt_includes_job_and_language(profile, make_job):
    profile["preferences"]["language"] = "Indonesian"
    prompt = score.build_prompt(make_job(title="Platform Engineer"), profile)
    assert "Platform Engineer" in prompt
    assert "in Indonesian" in prompt
    assert "Python" in prompt


def test_score_job_calls_endpoint_and_parses_reply(monkeypatch, profile, make_job):
    captured = {}

    class FakeResponse:
        text = _completion('{"score": 77, "reason": "Fits."}', 123)

        def raise_for_status(self):
            return None

    def fake_post(url, json, headers, timeout):
        captured.update(url=url, body=json, headers=headers)
        return FakeResponse()

    monkeypatch.setattr(score.requests, "post", fake_post)
    result, tokens = score.score_job(make_job(), profile, "http://router/v1/", "key", "job-scorer")

    assert result == {"score": 77, "reason": "Fits."}
    assert tokens == 123
    assert captured["url"] == "http://router/v1/chat/completions"
    assert captured["body"]["model"] == "job-scorer"
    assert captured["body"]["stream"] is False
    assert captured["headers"]["Authorization"] == "Bearer key"
