"""Scoring stage: rate each pre-filtered job against the candidate profile.

Requests go to an OpenAI-compatible endpoint (9router by default), so the
underlying provider can be swapped or failed over without code changes.
"""
import json
import logging
import re

import requests

from radar import config, db, profile
from radar.filters import HardFilter

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a careful job-matching assistant. Judge how well a job posting fits "
    "a candidate profile. Reply with a single JSON object and nothing else."
)

USER_PROMPT = """CANDIDATE
{summary}
Target roles: {roles}
Seniority sought: {levels}
Skills: {skills}
The candidate lives in Indonesia and is looking for remote work.

JOB POSTING
Title: {title}
Company: {company}
Location: {location}
Salary: {salary}
Tags: {tags}
Description: {description}

Scoring rubric:
- 80-100: title, skills and seniority fit well and the candidate can clearly apply from Indonesia.
- 60-79: reasonable fit with minor gaps.
- 30-59: weak fit.
- 0-29: poor fit, or the posting restricts residency or work authorization to other countries.
If the description requires residency or work authorization elsewhere, the score must be low.

Reply with JSON only:
{{"score": <0-100>, "reason": "<one sentence in {language}, at most 160 characters>"}}"""


def build_prompt(job, prof: dict) -> str:
    skills = "; ".join(f"{group}: {', '.join(items)}" for group, items in prof["skills"].items())
    return USER_PROMPT.format(
        summary=prof["summary"].strip(),
        roles=", ".join(prof["target_roles"]),
        levels=", ".join(prof["levels"]),
        skills=skills,
        title=job["title"],
        company=job["company"],
        location=job["location"] or "not stated",
        salary=job["salary"] or "not stated",
        tags=job["tags"] or "-",
        description=(job["description"] or "")[:1500],
        language=prof.get("preferences", {}).get("language", "English"),
    )


def extract_text(raw: str) -> str:
    """Return the assistant text from either a JSON body or an SSE stream.

    Some upstream providers answer with server-sent events even when
    ``stream`` is false, so both shapes are handled.
    """
    raw = raw.strip()
    if not raw.startswith("data:"):
        return json.loads(raw)["choices"][0]["message"]["content"]
    parts = []
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("data:") or line.endswith("[DONE]"):
            continue
        try:
            delta = json.loads(line[5:])["choices"][0].get("delta", {})
        except (ValueError, KeyError, IndexError):
            continue
        parts.append(delta.get("content") or "")
    return "".join(parts)


def extract_usage(raw: str) -> int:
    """Total tokens reported by the provider, or 0 when absent."""
    for line in reversed(raw.strip().splitlines()):
        payload = line.strip().removeprefix("data:").strip()
        try:
            usage = json.loads(payload).get("usage")
        except ValueError:
            continue
        if usage:
            return int(usage.get("total_tokens", 0))
    return 0


def parse_result(text: str) -> dict:
    """Parse the model's JSON reply into ``{"score": int, "reason": str}``."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("no JSON object in model reply")
    data = json.loads(match.group(0))
    return {
        "score": max(0, min(100, int(data["score"]))),
        "reason": str(data.get("reason", "")).strip()[:300],
    }


def score_job(job, prof: dict, base_url: str, api_key: str, model: str) -> tuple[dict, int]:
    body = {
        "model": model,
        "stream": False,
        "temperature": 0,
        "max_tokens": 600,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(job, prof)},
        ],
    }
    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        json=body,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=90,
    )
    response.raise_for_status()
    return parse_result(extract_text(response.text)), extract_usage(response.text)


def run(limit: int = 20) -> int:
    """Score up to ``limit`` unscored jobs that pass the hard filter. Returns tokens used."""
    base_url = config.get("ROUTER_BASE_URL", "http://localhost:20128/v1")
    api_key = config.require("ROUTER_API_KEY")
    model = config.get("SCORING_MODEL", "job-scorer")
    prof = profile.load()
    hard_filter = HardFilter(prof)
    conn = db.connect()

    pending = [job for job in db.unscored(conn) if hard_filter.check(job)[0]][:limit]
    log.info("scoring %d jobs with model=%s", len(pending), model)

    total_tokens = 0
    for job in pending:
        result, tokens = None, 0
        for attempt in (1, 2):
            try:
                result, tokens = score_job(job, prof, base_url, api_key, model)
                break
            except Exception as exc:
                log.warning("attempt %d failed for %r: %s", attempt, job["title"], exc)
        if result is None:
            continue
        total_tokens += tokens
        db.save_score(conn, job, result["score"], result["reason"])
        log.info("score=%d title=%r company=%r", result["score"], job["title"], job["company"])
    log.info("tokens used: %d", total_tokens)
    return total_tokens
