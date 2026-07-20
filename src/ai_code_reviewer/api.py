"""FastAPI service for the reviewer.

    uvicorn ai_code_reviewer.api:app --reload   # docs at /docs
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from .client import LLMClient, StructuredCallError
from .config import Settings
from .github import fetch_pr_diff
from .models import ReviewResult
from .reviewer import Reviewer

app = FastAPI(
    title="ai-code-reviewer",
    version="0.1.0",
    description="Reviews a code diff or public GitHub PR for real bugs + security issues.",
)

_origins = os.getenv("REVIEWER_CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_origin_regex=r"https://ai-code-reviewer[a-z0-9-]*\.vercel\.app|http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

_reviewer: Reviewer | None = None


def _get_reviewer() -> Reviewer:
    global _reviewer
    if _reviewer is None:
        _reviewer = Reviewer(LLMClient(Settings.from_env()))
    return _reviewer


class ReviewRequest(BaseModel):
    diff: str | None = Field(default=None, description="A unified diff to review.")
    pr: str | None = Field(default=None, description="Or a public PR ref: owner/repo#123.")

    @model_validator(mode="after")
    def _one_of(self):
        if not (self.diff or self.pr):
            raise ValueError("provide either 'diff' or 'pr'")
        return self


@app.get("/health")
def health() -> dict:
    return {"ok": True, "configured": bool(os.getenv("ANTHROPIC_API_KEY"))}


@app.post("/api/review", response_model=ReviewResult)
def review(req: ReviewRequest) -> ReviewResult:
    try:
        diff_text = req.diff or fetch_pr_diff(req.pr)  # type: ignore[arg-type]
        return _get_reviewer().review(diff_text)
    except StructuredCallError as exc:
        raise HTTPException(status_code=502, detail=f"model output error: {exc}") from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
