"""Diff parsing, the grounding filter, and metrics — all offline."""

from __future__ import annotations

import sys
from pathlib import Path

from conftest import FakeClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))

from metrics import caught_planted, clean_pass  # noqa: E402

from ai_code_reviewer.diff import parse_diff  # noqa: E402
from ai_code_reviewer.github import parse_pr_ref  # noqa: E402
from ai_code_reviewer.models import Review  # noqa: E402
from ai_code_reviewer.reviewer import Reviewer  # noqa: E402

SQL_DIFF = """diff --git a/db.py b/db.py
--- a/db.py
+++ b/db.py
@@ -5,2 +5,4 @@ def lookup(conn, name):
     cur = conn.cursor()
+    q = "SELECT * FROM t WHERE name = '" + name + "'"
+    cur.execute(q)
"""


# --- diff parser ------------------------------------------------------------
def test_parser_extracts_added_lines_with_new_numbers():
    p = parse_diff(SQL_DIFF)
    assert p.files == ["db.py"]
    lines = {(c.line, c.text.strip()[:20]) for c in p.changed_lines}
    assert (6, 'q = "SELECT * FROM t') in lines  # the injection line
    assert (7, "cur.execute(q)") in lines
    assert "    6 +" in p.annotated  # annotated with new-file line numbers


# --- grounding filter -------------------------------------------------------
def test_reviewer_drops_findings_on_unchanged_lines(review_with_one_real_one_fake):
    result = Reviewer(FakeClient(review_with_one_real_one_fake)).review(SQL_DIFF)
    lines = [f.line for f in result.review.findings]
    assert 6 in lines          # the real, grounded finding survives
    assert 999 not in lines    # the hallucinated one is filtered out
    assert result.changed_line_count == 2


def test_empty_diff_returns_no_findings(review_with_one_real_one_fake):
    result = Reviewer(FakeClient(review_with_one_real_one_fake)).review("")
    assert result.review.findings == [] and result.changed_line_count == 0


# --- metrics ----------------------------------------------------------------
def test_caught_planted_and_clean():
    result = Reviewer(FakeClient(_review_at(6, "security"))).review(SQL_DIFF)
    assert caught_planted(result, 6, "security").passed is True
    assert caught_planted(result, 40, "security").passed is False  # nowhere near

    clean = Reviewer(FakeClient(Review(summary="clean", findings=[]))).review(SQL_DIFF)
    assert clean_pass(clean).passed is True


def _review_at(line: int, category: str) -> Review:
    from ai_code_reviewer.models import Category, Finding, Severity

    return Review(summary="s", findings=[
        Finding(file="db.py", line=line, severity=Severity.high, category=Category(category),
                issue="x", suggestion="y", snippet="z")])


# --- github ref parsing -----------------------------------------------------
def test_pr_ref_parsing():
    assert parse_pr_ref("owner/repo#123") == ("owner", "repo", 123)
    assert parse_pr_ref("https://github.com/psf/requests/pull/6432") == ("psf", "requests", 6432)
