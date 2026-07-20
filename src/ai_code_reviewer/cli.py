"""`ai-review` CLI.

    ai-review diff --file changes.diff
    ai-review pr --ref "owner/repo#123"
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from .client import LLMClient
from .config import Settings
from .github import fetch_pr_diff
from .reviewer import Reviewer

app = typer.Typer(add_completion=False, help="AI code reviewer — real bugs + security, not style.")
console = Console()

_SEV_STYLE = {"critical": "bold red", "high": "red", "medium": "yellow", "low": "dim"}


@app.callback()
def _root() -> None:
    """AI code reviewer — flags real bugs + security issues in a diff or PR."""


def _print(result) -> None:
    r = result.review
    console.print(Panel(r.summary, title=f"Review — {result.changed_line_count} changed lines", border_style="cyan"))
    if not r.findings:
        console.print("[green]No issues found on the changed lines.[/]")
        return
    for f in r.findings:
        style = _SEV_STYLE.get(f.severity.value, "white")
        console.print(f"\n[{style}]{f.severity.value.upper()}[/] · {f.category.value} · [bold]{f.file}:{f.line}[/]")
        console.print(f"  [dim]{f.snippet.strip()}[/]")
        console.print(f"  {f.issue}")
        console.print(f"  [green]→ {f.suggestion}[/]")


@app.command()
def diff(file: Path = typer.Option(..., exists=True, readable=True, help="A unified diff file.")) -> None:
    result = Reviewer(LLMClient(Settings.from_env())).review(file.read_text())
    _print(result)


@app.command()
def pr(ref: str = typer.Option(..., "--ref", help="owner/repo#123 or a PR URL (public).")) -> None:
    with console.status(f"[bold]Fetching {ref}…"):
        diff_text = fetch_pr_diff(ref)
    result = Reviewer(LLMClient(Settings.from_env())).review(diff_text)
    _print(result)


if __name__ == "__main__":
    app()
