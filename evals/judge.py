"""LLM-as-judge for review quality — are the findings real and worth a human's time?
Complements the deterministic recall/precision on the planted set. Opus."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai_code_reviewer.config import Settings
from ai_code_reviewer.models import ReviewResult


class ReviewGrade(BaseModel):
    correctness: int = Field(ge=1, le=5, description="Are the findings real bugs, not false alarms?")
    usefulness: int = Field(ge=1, le=5, description="Would a reviewer act on these?")
    noise: int = Field(ge=1, le=5, description="5 = no nitpick/style noise; 1 = lots of it.")
    overall: int = Field(ge=1, le=5)
    rationale: str

    @property
    def mean(self) -> float:
        return round((self.correctness + self.usefulness + self.noise + self.overall) / 4, 2)


JUDGE_SYSTEM = (
    "You grade an AI code review. Reward findings that are genuine bugs/security "
    "issues; penalise false positives, hallucinated problems, and style/nitpick noise. "
    "Correctness is the most important axis. Score 1–5."
)


class ReviewJudge:
    def __init__(self, client) -> None:
        self._client = client

    def grade(self, result: ReviewResult) -> ReviewGrade:
        user = f"CODE REVIEW OUTPUT:\n{result.review.model_dump_json(indent=2)}"
        return self._client.structured(
            schema=ReviewGrade, system=JUDGE_SYSTEM, user=user, model=Settings.from_env().judge_model
        )
