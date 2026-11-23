"""Job-board adapters.

Every adapter returns a list of dicts with the same keys (see ``_job``), so the
rest of the pipeline is independent of any one provider's schema.
"""
import html
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable

import requests

HEADERS = {"User-Agent": "job-radar/0.1 (personal job search)"}
TIMEOUT = 20


def _clean(text: str | None, limit: int = 2000) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _job(source, external_id, title, company, location, url, tags, salary, posted_at, description):
    return {
        "source": source,
        "external_id": str(external_id),
        "title": (title or "").strip(),
        "company": (company or "").strip(),
        "location": (location or "").strip(),
        "url": url or "",
        "tags": ",".join(tags) if isinstance(tags, list) else (tags or ""),
        "salary": salary or "",
        "posted_at": posted_at or "",
        "description": _clean(description),
    }


def fetch_remotive() -> list[dict]:
    """Remotive public API (software-dev and data categories).

    The provider asks consumers to poll sparingly and to credit the source.
    """
    jobs = []
    for category in ("software-dev", "data"):
        response = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": category},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        for item in response.json().get("jobs", []):
            jobs.append(
                _job(
                    "remotive", item["id"], item["title"], item["company_name"],
                    item.get("candidate_required_location"), item["url"], item.get("tags", []),
                    item.get("salary"), item.get("publication_date"), item.get("description"),
                )
            )
    return jobs


def fetch_remoteok() -> list[dict]:
    """Remote OK public API. The first array element is a legal notice and is skipped."""
    response = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    jobs = []
    for item in response.json()[1:]:
        salary = ""
        if item.get("salary_min") or item.get("salary_max"):
            salary = f"{item.get('salary_min', '')}-{item.get('salary_max', '')} USD"
        jobs.append(
            _job(
                "remoteok", item["id"], item.get("position"), item.get("company"),
                item.get("location"), item.get("url"), item.get("tags", []),
                salary, item.get("date"), item.get("description"),
            )
        )
    return jobs


def parse_weworkremotely(xml_bytes: bytes) -> list[dict]:
    """Parse a We Work Remotely RSS document."""
    root = ET.fromstring(xml_bytes)
    jobs = []
    for item in root.iter("item"):
        raw_title = item.findtext("title") or ""
        company, _, title = raw_title.partition(": ")
        if not title:
            company, title = "", raw_title
        jobs.append(
            _job(
                "wwr", item.findtext("guid") or item.findtext("link"), title, company,
                item.findtext("region"), item.findtext("link"), [],
                "", item.findtext("pubDate"), item.findtext("description"),
            )
        )
    return jobs


def fetch_weworkremotely() -> list[dict]:
    """We Work Remotely RSS feed (programming category)."""
    response = requests.get(
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return parse_weworkremotely(response.content)


SOURCES: dict[str, Callable[[], list[dict]]] = {
    "remotive": fetch_remotive,
    "remoteok": fetch_remoteok,
    "wwr": fetch_weworkremotely,
}
