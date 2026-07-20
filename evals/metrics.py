"""Deterministic reviewer evals — no model calls.

Two axes a review bot lives or dies on:
  RECALL — does it CATCH a known planted bug (a finding on/near the planted line)?
  PRECISION — does it stay QUIET on a clean diff (no false-positive noise)?
A bot with great recall but poor precision gets muted by the team, so both matter.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_code_reviewer.models import ReviewResult


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def caught_planted(result: ReviewResult, line: int, category: str, tolerance: int = 1) -> CheckResult:
    """Did any finding land on/near the planted bug's line?"""
    near = [f for f in result.review.findings if abs(f.line - line) <= tolerance]
    same_cat = [f for f in near if f.category.value == category]
    if same_cat:
        return CheckResult("caught_planted", True, f"caught at line {same_cat[0].line} ({category})")
    if near:
        return CheckResult(
            "caught_planted", True, f"caught at line {near[0].line} (as {near[0].category.value}, not {category})"
        )
    return CheckResult("caught_planted", False, f"MISSED the planted {category} bug at line {line}")


def clean_pass(result: ReviewResult) -> CheckResult:
    """A clean diff should produce no findings (no false-positive noise)."""
    n = len(result.review.findings)
    return CheckResult(
        "clean_no_false_positives",
        n == 0,
        "ok — stayed quiet" if n == 0 else f"{n} false-positive finding(s) on a clean diff",
    )
