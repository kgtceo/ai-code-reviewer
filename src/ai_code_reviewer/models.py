"""Typed contracts for the reviewer.

`Review` is the tool schema the model fills, so findings come back as structured
data — each tied to a real changed line (validated), with a severity and category.
The grounding rule (recurring across the portfolio): a finding must point at a line
that's actually in the diff, or it's noise.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Category(str, Enum):
    bug = "bug"
    security = "security"
    correctness = "correctness"
    performance = "performance"


class Finding(BaseModel):
    file: str = Field(description="Path of the changed file the issue is in.")
    line: int = Field(description="A line number that this diff ADDS or changes.")
    severity: Severity
    category: Category
    issue: str = Field(description="What's wrong, specifically.")
    suggestion: str = Field(description="How to fix it.")
    snippet: str = Field(description="The exact changed line the finding refers to (verbatim).")


class Review(BaseModel):
    summary: str = Field(description="1–2 sentences: is this diff safe to merge, and the biggest risk.")
    findings: list[Finding] = Field(default_factory=list)


class ChangedLine(BaseModel):
    file: str
    line: int  # line number in the NEW file
    text: str


class ReviewResult(BaseModel):
    review: Review
    files_reviewed: list[str] = Field(default_factory=list)
    changed_line_count: int = 0
