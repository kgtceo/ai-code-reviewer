"""Reviewer scorecard: recall on planted bugs + precision on clean diffs + LLM judge.

    python evals/run_evals.py               # full (+ judge)
    python evals/run_evals.py --no-judge    # deterministic only (cheap, CI-gateable)

Needs ANTHROPIC_API_KEY. Non-zero exit if a gate check fails. Reports → evals/reports/.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

from judge import ReviewJudge  # noqa: E402
from metrics import caught_planted, clean_pass  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from ai_code_reviewer.client import LLMClient  # noqa: E402
from ai_code_reviewer.config import Settings  # noqa: E402
from ai_code_reviewer.reviewer import Reviewer  # noqa: E402

console = Console()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-judge", action="store_true")
    args = parser.parse_args()

    settings = Settings.from_env()
    client = LLMClient(settings)
    reviewer = Reviewer(client)
    judge = None if args.no_judge else ReviewJudge(client)
    cases = json.loads((HERE / "dataset" / "cases.json").read_text())

    rows, gate_ok = [], True
    recall_hit = recall_total = clean_hit = clean_total = 0
    for c in cases:
        diff_text = (HERE / "dataset" / c["diff"]).read_text()
        with console.status(f"[bold]Reviewing {c['name']}…"):
            result = reviewer.review(diff_text)
        if c["planted"]:
            recall_total += 1
            chk = caught_planted(result, c["planted"]["line"], c["planted"]["category"])
            recall_hit += chk.passed
        else:
            clean_total += 1
            chk = clean_pass(result)
            clean_hit += chk.passed
        gate_ok &= chk.passed
        grade = judge.grade(result) if judge else None
        rows.append((c["name"], len(result.review.findings), chk, grade))

    table = Table(title="Code-review scorecard", show_lines=True)
    for col in ("Case", "# findings", "Gate", "Judge/5"):
        table.add_column(col)
    for name, nf, chk, grade in rows:
        table.add_row(name, str(nf), "✓" if chk.passed else "✗", str(grade.mean) if grade else "—")
    console.print(table)
    console.print(
        f"recall (planted bugs caught): {recall_hit}/{recall_total}  ·  "
        f"precision (clean diffs kept quiet): {clean_hit}/{clean_total}"
    )
    for name, _nf, chk, _g in rows:
        if not chk.passed:
            console.print(f"  [red]✗[/] {name}: {chk.detail}")

    reports = HERE / "reports"
    reports.mkdir(exist_ok=True)
    out = reports / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(
        [{"name": n, "findings": nf, "passed": chk.passed, "detail": chk.detail,
          "judge": (g.model_dump() if g else None)} for n, nf, chk, g in rows], indent=2))
    console.print(f"[dim]report → {out.relative_to(HERE.parent)}[/]")
    return 0 if gate_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
