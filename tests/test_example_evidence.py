"""Example evidence and reviews must match the schemas and the plan they belong to."""

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "spec" / "schema"
EXAMPLES = [
    ROOT / "spec" / "examples" / "ambient-scribe",
    ROOT / "spec" / "examples" / "ambient-scribe-illustrative",
]
ILLUSTRATIVE = EXAMPLES[1]
LABEL = "NOT REAL RESULTS / FOR EDUCATIONAL PURPOSES"


def _schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def _plan(example: Path) -> dict[str, Any]:
    return yaml.safe_load((example / "athlon.yaml").read_text(encoding="utf-8"))


def _records(example: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for path in sorted((example / "evidence").glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _with_evidence() -> list[Path]:
    return [e for e in EXAMPLES if list((e / "evidence").glob("*.jsonl"))]


def _with_review() -> list[Path]:
    return [e for e in EXAMPLES if (e / "review.yaml").is_file()]


def _ids(examples: list[Path]) -> list[str]:
    return [e.name for e in examples]


@pytest.mark.parametrize("example", _with_evidence(), ids=_ids(_with_evidence()))
def test_evidence_matches_schema(example: Path) -> None:
    validator = Draft202012Validator(_schema("evidence"))
    for record in _records(example):
        errors = [e.message for e in validator.iter_errors(record)]
        assert not errors, (record["subject"], errors)


@pytest.mark.parametrize("example", _with_evidence(), ids=_ids(_with_evidence()))
def test_evidence_references_the_plan(example: Path) -> None:
    plan = _plan(example)
    events = {e["id"]: e for e in plan["events"]}
    measures = {b["id"]: {m["id"] for m in b["measures"]} for b in plan["blocks"]}
    for record in _records(example):
        event = events[record["event"]]
        assert (event.get("extensions") or {}).get("status") != "declared_not_run"
        assert record["tool"] in event["tools"]
        assert record["block"] in event["blocks"]
        assert record["measure"] in measures[record["block"]]
        for factor, level in record["conditions"].items():
            assert level in event["conditions"][factor], (factor, level)


@pytest.mark.parametrize("example", _with_evidence(), ids=_ids(_with_evidence()))
def test_evidence_source_hash_matches_its_file(example: Path) -> None:
    for record in _records(example):
        source = example / record["source"]["uri"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == record["source"]["sha256"]


@pytest.mark.parametrize("example", _with_review(), ids=_ids(_with_review()))
def test_review_matches_schema_and_answers_every_question(example: Path) -> None:
    review = yaml.safe_load((example / "review.yaml").read_text(encoding="utf-8"))
    errors = [e.message for e in Draft202012Validator(_schema("review")).iter_errors(review)]
    assert not errors, errors
    plan = _plan(example)
    assert review["athlon"] == plan["id"]
    asked = {q["id"] for q in plan["interrogation"]}
    answered = {r["question"] for r in review["interrogation"]}
    assert answered == asked


def test_illustrative_data_is_labeled_everywhere() -> None:
    for record in _records(ILLUSTRATIVE):
        assert record["extensions"]["illustrative"] is True
        assert record["extensions"]["label"] == LABEL
    for name in ("athlon.yaml", "review.yaml", "overview.html", "README.md"):
        assert LABEL in (ILLUSTRATIVE / name).read_text(encoding="utf-8"), name
    assert (
        yaml.safe_load((ILLUSTRATIVE / "review.yaml").read_text())["extensions"]["label"] == LABEL
    )


def test_illustrative_files_match_the_generator() -> None:
    spec = importlib.util.spec_from_file_location("generate", ILLUSTRATIVE / "generate.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name, text in module.render_all().items():
        committed = (ILLUSTRATIVE / name).read_text(encoding="utf-8")
        assert committed == text, f"{name} is stale; run generate.py"
