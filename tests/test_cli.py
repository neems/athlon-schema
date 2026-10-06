"""CLI tests via Typer's CliRunner."""

import json
from pathlib import Path
from typing import Any

import yaml
from typer.testing import CliRunner

from tevv_athlon import __version__
from tevv_athlon.cli import app
from tevv_athlon.model import FRAMEWORK_REF, SPEC_VERSION

runner = CliRunner()


def plan() -> dict[str, Any]:
    return {
        "spec_version": SPEC_VERSION,
        "framework_ref": FRAMEWORK_REF,
        "id": "demo",
        "title": "Demo",
        "system": {"name": "Bot", "description": "A bot."},
        "lifecycle_stage": "build_use",
        "goals": {"q1": "Goal.", "q2": "Who cares."},
        "characteristics": [{"id": "safe", "kind": "trustworthiness"}],
        "blocks": [
            {
                "id": "b1",
                "characteristics": ["safe"],
                "definition": "d",
                "evidence_required": "e",
                "measures": [{"id": "m1", "unit": "proportion", "direction": "neutral"}],
            }
        ],
        "events": [
            {
                "id": "e1",
                "type": "benchmark",
                "setting": "controlled",
                "blocks": ["b1"],
                "tools": ["t1"],
            }
        ],
        "toolbox": [{"id": "t1", "kind": "eval_harness", "ref": {"name": "x"}}],
        "interrogation": [{"id": "q1", "question": "Valid?"}],
    }


def write(tmp_path: Path, data: dict[str, Any]) -> Path:
    path = tmp_path / "athlon.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_validate_clean_exits_0(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate", str(write(tmp_path, plan()))])
    assert result.exit_code == 0, result.output
    assert "error" not in result.stdout


def test_validate_warnings_only_exits_0(tmp_path: Path) -> None:
    data = plan()
    data["interrogation"] = []
    result = runner.invoke(app, ["validate", str(write(tmp_path, data))])
    assert result.exit_code == 0, result.output
    assert "warning W201 /interrogation: Plan has no interrogation questions" in result.stdout


def test_validate_error_exits_1(tmp_path: Path) -> None:
    data = plan()
    data["events"][0]["blocks"] = ["b1", "nope"]
    result = runner.invoke(app, ["validate", str(write(tmp_path, data))])
    assert result.exit_code == 1
    assert "error E101 /events/0/blocks/1: Unknown block 'nope'" in result.stdout


def test_validate_unparseable_exits_1(tmp_path: Path) -> None:
    path = tmp_path / "athlon.yaml"
    path.write_text("- just\n- a list\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", str(path)])
    assert result.exit_code == 1
    assert "E001" in result.stdout


def test_validate_missing_file_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate", str(tmp_path / "missing.yaml")])
    assert result.exit_code == 2


def test_validate_bad_format_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate", str(write(tmp_path, plan())), "--format", "xml"])
    assert result.exit_code == 2


def test_validate_json_output(tmp_path: Path) -> None:
    data = plan()
    data["events"][0]["tools"] = ["t1", "ghost"]
    data["interrogation"] = []
    result = runner.invoke(app, ["validate", str(write(tmp_path, data)), "--format", "json"])
    assert result.exit_code == 1
    issues = json.loads(result.stdout)
    assert isinstance(issues, list)
    assert all(set(i) == {"path", "code", "severity", "message"} for i in issues)
    assert {
        "path": "/events/0/tools/1",
        "code": "E102",
        "severity": "error",
        "message": "Unknown tool 'ghost'",
    } in issues
    assert any(i["code"] == "W201" and i["severity"] == "warning" for i in issues)


def test_validate_json_clean_is_empty_array(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate", str(write(tmp_path, plan())), "--format", "json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_schema_export_and_check(tmp_path: Path) -> None:
    out = tmp_path / "schema"
    result = runner.invoke(app, ["schema", "export", "--check", "--out", str(out)])
    assert result.exit_code == 1
    assert not out.exists()

    result = runner.invoke(app, ["schema", "export", "--out", str(out)])
    assert result.exit_code == 0, result.output
    files = sorted(p.name for p in out.iterdir())
    assert files == ["athlon.schema.json", "evidence.schema.json", "review.schema.json"]

    result = runner.invoke(app, ["schema", "export", "--check", "--out", str(out)])
    assert result.exit_code == 0, result.output

    target = out / "review.schema.json"
    target.write_text(target.read_text(encoding="utf-8").replace("review", "reveiw"), "utf-8")
    before = target.read_bytes()
    result = runner.invoke(app, ["schema", "export", "--check", "--out", str(out)])
    assert result.exit_code == 1
    assert "review.schema.json" in result.output
    assert target.read_bytes() == before


def test_codes_json_lists_all() -> None:
    from tevv_athlon.validate import ISSUE_CODES

    result = runner.invoke(app, ["codes", "--format", "json"])
    assert result.exit_code == 0
    rows = json.loads(result.stdout)
    assert {r["code"] for r in rows} == set(ISSUE_CODES)
    assert all(set(r) == {"code", "severity", "title", "hint"} for r in rows)


def test_codes_single_and_unknown() -> None:
    from tevv_athlon.validate import ISSUE_CATALOG

    ok = runner.invoke(app, ["codes", "E101"])
    assert ok.exit_code == 0
    assert ISSUE_CATALOG["E101"].hint in ok.stdout.replace("\n", " ").replace("  ", " ")
    assert runner.invoke(app, ["codes", "E999"]).exit_code == 2
