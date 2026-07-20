"""Offline fixtures — a fake client returning a preset Review (no network)."""

from __future__ import annotations

import pytest

from ai_code_reviewer.models import Category, Finding, Review, Severity


class FakeClient:
    def __init__(self, review: Review) -> None:
        self._review = review
        self.last_user: str | None = None

    def structured(self, *, schema, system, user, model=None):
        self.last_user = user
        return self._review


@pytest.fixture
def review_with_one_real_one_fake() -> Review:
    # One finding on a real changed line (6), one on a line the diff never touched (999).
    return Review(
        summary="One real issue.",
        findings=[
            Finding(file="db.py", line=6, severity=Severity.critical, category=Category.security,
                    issue="SQL injection via string concatenation.", suggestion="Use a parameterised query.",
                    snippet="q = \"SELECT * FROM t WHERE name = '\" + name + \"'\""),
            Finding(file="db.py", line=999, severity=Severity.low, category=Category.bug,
                    issue="hallucinated finding on a non-existent line", suggestion="n/a", snippet="ghost"),
        ],
    )
