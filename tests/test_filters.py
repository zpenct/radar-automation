import pytest

from radar.filters import HardFilter


@pytest.fixture
def hard_filter(profile):
    return HardFilter(profile)


def test_matching_job_passes(hard_filter, make_job):
    assert hard_filter.check(make_job()) == (True, "passed")


def test_title_outside_target_roles_is_rejected(hard_filter, make_job):
    ok, reason = hard_filter.check(make_job(title="Account Executive"))
    assert not ok and "target roles" in reason


def test_seniority_exclusion(hard_filter, make_job):
    ok, reason = hard_filter.check(make_job(title="Senior Backend Engineer"))
    assert not ok and "excluded" in reason


def test_whole_word_matching_avoids_false_positives(hard_filter, make_job):
    # "ai" must not match inside "Mail", otherwise unrelated titles would pass.
    ok, _ = hard_filter.check(make_job(title="Mail Clerk"))
    assert not ok


def test_blocked_location_is_rejected(hard_filter, make_job):
    ok, reason = hard_filter.check(make_job(location="US Only"))
    assert not ok and "location" in reason


def test_allow_term_overrides_block_term(hard_filter, make_job):
    ok, _ = hard_filter.check(make_job(location="Remote, UK"))
    assert ok


def test_unknown_or_empty_location_passes_to_the_model(hard_filter, make_job):
    assert hard_filter.check(make_job(location=""))[0]
    assert hard_filter.check(make_job(location="Arlington"))[0]


def test_description_residency_requirement_is_rejected(hard_filter, make_job):
    ok, reason = hard_filter.check(make_job(description="You must reside in Texas."))
    assert not ok and "residency" in reason
