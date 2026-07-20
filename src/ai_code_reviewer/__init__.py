"""ai-code-reviewer — flags real bugs + security issues in a diff/PR, grounded in the
actual changed lines, with a planted-bug eval suite."""

from .diff import parse_diff
from .models import Category, Finding, Review, ReviewResult, Severity
from .reviewer import Reviewer

__all__ = [
    "Category",
    "Finding",
    "Review",
    "ReviewResult",
    "Reviewer",
    "Severity",
    "parse_diff",
]
__version__ = "0.1.0"
