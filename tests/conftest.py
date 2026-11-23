import pytest

from radar import db


@pytest.fixture
def profile():
    return {
        "summary": "Backend engineer.",
        "skills": {"languages": ["Python"], "infra": ["Docker"]},
        "target_roles": ["Backend Engineer"],
        "levels": ["junior", "mid"],
        "preferences": {"language": "English", "min_score": 60},
        "filters": {
            "title_include": ["engineer", "developer", "ai"],
            "title_exclude": ["senior", "manager"],
            "location_allow": ["worldwide", "anywhere", "remote"],
            "location_block": ["us only", "europe", "uk"],
            "description_exclude": ["security clearance", "must reside in"],
        },
    }


@pytest.fixture
def make_job():
    def _make(**overrides):
        job = {
            "source": "remotive",
            "external_id": "1",
            "title": "Backend Engineer",
            "company": "Acme",
            "location": "Worldwide",
            "url": "https://example.com/jobs/1",
            "tags": "python,docker",
            "salary": "",
            "posted_at": "2026-01-01",
            "description": "Build APIs.",
        }
        job.update(overrides)
        return job

    return _make


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(tmp_path / "jobs.db")
    yield connection
    connection.close()
