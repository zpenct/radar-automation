"""Rule-based pre-filter.

Runs before any model call so that clearly irrelevant postings never consume tokens.
"""
import re
from collections.abc import Mapping


def _compile(words: list[str] | None):
    """Build a case-insensitive whole-word matcher (so "ai" does not match "mail")."""
    if not words:
        return None
    alternation = "|".join(re.escape(word) for word in words)
    return re.compile(rf"(?<![\w])(?:{alternation})(?![\w])", re.I)


class HardFilter:
    def __init__(self, profile: Mapping):
        rules = profile["filters"]
        self._title_include = _compile(rules.get("title_include"))
        self._title_exclude = _compile(rules.get("title_exclude"))
        self._location_allow = _compile(rules.get("location_allow"))
        self._location_block = _compile(rules.get("location_block"))
        self._description_exclude = _compile(rules.get("description_exclude"))

    def check(self, job: Mapping) -> tuple[bool, str]:
        """Return ``(passed, reason)`` for a job."""
        title = job["title"] or ""
        location = job["location"] or ""
        description = job["description"] or ""

        if self._title_include and not self._title_include.search(title):
            return False, "title outside target roles"
        if self._title_exclude and self._title_exclude.search(title):
            return False, "title excluded (level or domain)"
        # An explicit "allow" term wins over a "block" term. Unknown or empty
        # locations pass through and are judged by the model later.
        if location and self._location_block and self._location_block.search(location):
            if not (self._location_allow and self._location_allow.search(location)):
                return False, "location excludes the candidate's region"
        if self._description_exclude and self._description_exclude.search(description):
            return False, "description requires residency elsewhere"
        return True, "passed"
