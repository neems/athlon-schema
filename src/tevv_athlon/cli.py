"""Command line entry point for tevv-athlon."""

import json
from dataclasses import asdict
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from tevv_athlon import __version__
from tevv_athlon import schema as schema_mod
from tevv_athlon.validate import ISSUE_CATALOG, validate_plan_file

app = typer.Typer(help="tevv-athlon", add_completion=False, no_args_is_help=True)
schema_app = typer.Typer(help="Work with the published JSON Schemas.", no_args_is_help=True)
app.add_typer(schema_app, name="schema")


class OutputFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = False,
) -> None:
    """tevv-athlon command line."""


@app.command()
def validate(
    path: Annotated[
        Path,
        typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, help="Plan file."
        ),
    ],
    output_format: Annotated[
        OutputFormat, typer.Option("--format", help="Output format.")
    ] = OutputFormat.TEXT,
) -> None:
    """Validate an athlon.yaml plan. Exit 0 if no errors, 1 if any error, 2 on usage error."""
    issues = validate_plan_file(path)
    if output_format is OutputFormat.JSON:
        typer.echo(json.dumps([asdict(i) for i in issues], indent=2))
    else:
        for i in issues:
            typer.echo(f"{i.severity} {i.code} {i.path or '/'}: {i.message}")
        errors = sum(1 for i in issues if i.severity == "error")
        warnings = len(issues) - errors
        typer.echo(f"{path}: {errors} error(s), {warnings} warning(s)", err=True)
    if any(i.severity == "error" for i in issues):
        raise typer.Exit(1)


@app.command()
def codes(
    code: Annotated[str | None, typer.Argument(help="Show only this issue code.")] = None,
    output_format: Annotated[
        OutputFormat, typer.Option("--format", help="Output format.")
    ] = OutputFormat.TEXT,
) -> None:
    """List issue codes with severity, title and fix hint. Exit 2 on unknown code."""
    selected = list(ISSUE_CATALOG)
    if code is not None:
        if code not in ISSUE_CATALOG:
            typer.echo(f"Unknown code '{code}'. Known: {', '.join(ISSUE_CATALOG)}", err=True)
            raise typer.Exit(2)
        selected = [code]
    rows = [
        {
            "code": c,
            "severity": "warning" if c.startswith("W") else "error",
            "title": ISSUE_CATALOG[c].title,
            "hint": ISSUE_CATALOG[c].hint,
        }
        for c in selected
    ]
    if output_format is OutputFormat.JSON:
        typer.echo(json.dumps(rows, indent=2))
        return
    for r in rows:
        typer.echo(f"{r['code']} {r['severity']}: {r['title']}\n    Fix: {r['hint']}")


@schema_app.command("export")
def schema_export(
    out: Annotated[Path, typer.Option("--out", file_okay=False, help="Output directory.")] = Path(
        "spec/schema"
    ),
    check: Annotated[
        bool, typer.Option("--check", help="Write nothing; exit 1 if files are stale.")
    ] = False,
) -> None:
    """Generate JSON Schemas from the models into OUT."""
    if check:
        stale = schema_mod.check(out)
        if stale:
            for p in stale:
                typer.echo(f"stale: {p}", err=True)
            typer.echo("Run `tevv-athlon schema export` to regenerate.", err=True)
            raise typer.Exit(1)
        typer.echo(f"{out}: schemas up to date")
        return
    for p in schema_mod.export(out):
        typer.echo(f"wrote {p}")
