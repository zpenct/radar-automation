from radar import sources

RSS = b"""<?xml version="1.0"?>
<rss><channel>
  <item>
    <title>Acme: Backend Engineer</title>
    <region>Anywhere in the World</region>
    <guid>https://example.com/1</guid>
    <link>https://example.com/1</link>
    <pubDate>Mon, 01 Jan 2026 00:00:00 +0000</pubDate>
    <description>&lt;p&gt;Build &amp;amp; ship APIs.&lt;/p&gt;</description>
  </item>
  <item>
    <title>Untitled posting</title>
    <guid>https://example.com/2</guid>
    <link>https://example.com/2</link>
  </item>
</channel></rss>"""


def test_clean_strips_tags_and_entities_and_truncates():
    assert sources._clean("<p>Fish &amp; <b>chips</b></p>") == "Fish & chips"
    assert len(sources._clean("x" * 5000, limit=100)) == 100
    assert sources._clean(None) == ""


def test_parse_weworkremotely_splits_company_and_title():
    jobs = sources.parse_weworkremotely(RSS)
    assert jobs[0]["company"] == "Acme"
    assert jobs[0]["title"] == "Backend Engineer"
    assert jobs[0]["location"] == "Anywhere in the World"
    assert jobs[0]["description"] == "Build & ship APIs."


def test_parse_weworkremotely_handles_titles_without_company():
    jobs = sources.parse_weworkremotely(RSS)
    assert jobs[1]["company"] == ""
    assert jobs[1]["title"] == "Untitled posting"


def test_fetch_remoteok_skips_legal_notice_and_formats_salary(monkeypatch):
    payload = [
        {"legal": "terms"},
        {"id": 7, "position": "Dev", "company": "Co", "location": "Worldwide",
         "url": "https://r.ok/7", "tags": ["python"], "salary_min": 50000,
         "salary_max": 90000, "date": "2026-01-01", "description": "<b>Hi</b>"},
    ]

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return payload

    monkeypatch.setattr(sources.requests, "get", lambda *a, **k: FakeResponse())
    jobs = sources.fetch_remoteok()

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "7"
    assert jobs[0]["salary"] == "50000-90000 USD"
    assert jobs[0]["tags"] == "python"
