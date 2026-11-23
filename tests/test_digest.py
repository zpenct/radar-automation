from radar import digest


def _row(make_job, **overrides):
    return {**make_job(), "score": 88, "reason": "Strong match.", **overrides}


def test_empty_selection_renders_empty_string():
    assert digest.format_digest([]) == ""


def test_entry_contains_key_fields(make_job):
    text = digest.format_digest([_row(make_job, salary="$4k/month")])
    assert "Backend Engineer - Acme (88/100)" in text
    assert "Strong match." in text
    assert "Salary: $4k/month" in text
    assert "Source: Remotive" in text
    assert "https://example.com/jobs/1" in text


def test_salary_line_is_omitted_when_missing(make_job):
    assert "Salary" not in digest.format_digest([_row(make_job)])


def test_preview_header_differs_from_regular(make_job):
    rows = [_row(make_job)]
    assert "preview" in digest.format_digest(rows, preview=True)
    assert "preview" not in digest.format_digest(rows)


def test_unknown_source_falls_back_to_raw_name(make_job):
    text = digest.format_digest([_row(make_job, source="newboard")])
    assert "Source: newboard" in text
