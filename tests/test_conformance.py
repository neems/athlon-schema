"""Conformance: CLI validation plus an independent JSON Schema check."""

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tevv_athlon.cli import app

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "spec" / "schema" / "athlon.schema.json"
FIXTURES = ROOT / "tests" / "fixtures"
GOOD = sorted((ROOT / "spec" / "examples").glob("*/athlon.yaml")) + [
    FIXTURES / "query-violation" / "athlon.yaml"
]
BROKEN = FIXTURES / "broken" / "athlon.yaml"

runner = CliRunner()


def test_examples_found() -> None:
    assert len(GOOD) >= 2


@pytest.mark.parametrize("path", GOOD, ids=lambda p: p.parent.name)
def test_cli_validate_passes(path: Path) -> None:
    result = runner.invoke(app, ["validate", str(path)])
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize("path", GOOD, ids=lambda p: p.parent.name)
def test_check_jsonschema_passes(path: Path) -> None:
    proc = subprocess.run(
        ["check-jsonschema", "--schemafile", str(SCHEMA), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_broken_fixture_reports_expected_codes() -> None:
    result = runner.invoke(app, ["validate", str(BROKEN), "--format", "json"])
    assert result.exit_code == 1
    codes = {issue["code"] for issue in json.loads(result.stdout)}
    assert codes == {"E101", "E102", "E104", "E107"}
