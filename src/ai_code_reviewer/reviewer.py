"""The review pipeline: diff -> parse -> grounded structured review.

After the model returns findings, we DROP any finding whose (file, line) isn't an
actually-changed line — a deterministic grounding filter so the reviewer can't invent
comments on lines that don't exist in the diff. Pure orchestration, so it's
unit-testable with a fake client.
"""

from __future__ import annotations

from . import prompts
from .client import LLMClient
from .diff import parse_diff
from .models import Review, ReviewResult


class Reviewer:
    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def review(self, diff_text: str) -> ReviewResult:
        parsed = parse_diff(diff_text)
        if not parsed.changed_lines:
            return ReviewResult(
                review=Review(summary="No added/changed lines to review.", findings=[]),
                files_reviewed=parsed.files,
                changed_line_count=0,
            )

        review = self._client.structured(
            schema=Review,
            system=prompts.REVIEW_SYSTEM,
            user=prompts.review_user(parsed.annotated),
        )

        # Grounding filter: keep only findings that point at a real changed line.
        changed = {(c.file, c.line) for c in parsed.changed_lines}
        review.findings = [f for f in review.findings if (f.file, f.line) in changed]

        return ReviewResult(
            review=review,
            files_reviewed=parsed.files,
            changed_line_count=len(parsed.changed_lines),
        )
