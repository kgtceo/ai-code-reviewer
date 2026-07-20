"""Unified-diff parser.

Two jobs: (1) extract the ADDED lines with their real NEW-file line numbers, so we
can validate that a finding points at a line the diff actually changed (grounding),
and (2) render an annotated diff where each kept/added line is prefixed with its new
line number, so the model can cite line numbers accurately instead of guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ChangedLine

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass
class ParsedDiff:
    files: list[str]
    changed_lines: list[ChangedLine]  # added lines only, with NEW line numbers
    annotated: str  # human/LLM-readable diff with new-file line numbers


def parse_diff(diff_text: str) -> ParsedDiff:
    files: list[str] = []
    changed: list[ChangedLine] = []
    out: list[str] = []
    current_file: str | None = None
    new_line = 0

    for raw in diff_text.splitlines():
        if raw.startswith("+++ "):
            # +++ b/path/to/file  (or /dev/null for deletions)
            path = raw[4:].strip()
            path = path[2:] if path.startswith(("a/", "b/")) else path
            current_file = None if path == "/dev/null" else path
            if current_file and current_file not in files:
                files.append(current_file)
            out.append(raw)
            continue
        if raw.startswith("--- ") or raw.startswith("diff --git") or raw.startswith("index "):
            out.append(raw)
            continue
        m = _HUNK.match(raw)
        if m:
            new_line = int(m.group(1))
            out.append(raw)
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            text = raw[1:]
            if current_file:
                changed.append(ChangedLine(file=current_file, line=new_line, text=text))
            out.append(f"{new_line:>5} + {text}")
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            out.append(f"      - {raw[1:]}")  # removed line: no new-file number
        else:  # context
            out.append(f"{new_line:>5}   {raw[1:] if raw.startswith(' ') else raw}")
            new_line += 1

    return ParsedDiff(files=files, changed_lines=changed, annotated="\n".join(out))
