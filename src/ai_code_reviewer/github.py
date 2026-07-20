"""Fetch a public GitHub PR as a unified diff — so the reviewer works on real PRs,
not just pasted diffs. Uses GitHub's `.diff` endpoint (no token needed for public
repos)."""

from __future__ import annotations

import re

_PR = re.compile(
    r"(?:https?://github\.com/)?([\w.-]+)/([\w.-]+)(?:/pull/|#)(\d+)"
)


def parse_pr_ref(ref: str) -> tuple[str, str, int]:
    """Accept 'owner/repo#123' or a full PR URL → (owner, repo, number)."""
    m = _PR.search(ref.strip())
    if not m:
        raise ValueError(f"Not a PR reference: {ref!r} (try owner/repo#123 or a PR URL)")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_pr_diff(ref: str, *, timeout: float = 15.0) -> str:
    import httpx

    owner, repo, number = parse_pr_ref(ref)
    url = f"https://github.com/{owner}/{repo}/pull/{number}.diff"
    with httpx.Client(timeout=timeout, follow_redirects=True) as c:
        resp = c.get(url, headers={"User-Agent": "ai-code-reviewer/0.1"})
    resp.raise_for_status()
    return resp.text
