"""Tests for the plan validator: one focused test per issue code."""

import copy
from pathlib import Path
from typing import Any

from tevv_athlon.model import FRAMEWORK_REF, SPEC_VERSION
from tevv_athlon.validate import ISSUE_CODES, Issue, validate_plan_data, validate_plan_file


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
        "toolbox": [
            {
                "id": "t1",
                "kind": "eval_harness",
                "ref": {"name": "x"},
                "adapter": {"type": "tabular", "map": {"rate": "m1"}},
            }
        ],
        "interrogation": [{"id": "q1", "question": "Valid?"}],
    }


def issues_for(data: dict[str, Any]) -> list[Issue]:
    return validate_plan_data(data)


def codes(data: dict[str, Any]) -> list[tuple[str, str]]:
    return [(i.code, i.path) for i in issues_for(data)]


def test_clean_plan() -> None:
    assert issues_for(plan()) == []


def test_code_table_covers_all_codes() -> None:
    assert set(ISSUE_CODES) == {
        "E001",
        "E002",
        "E003",
        "E101",
        "E102",
        "E103",
        "E104",
        "E105",
        "E106",
        "E107",
        "E108",
        "E109",
        "W201",
        "W202",
    }


def test_e001_bad_yaml(tmp_path: Path) -> None:
    f = tmp_path / "a.yaml"
    f.write_text("a: [unclosed\n")
    assert [i.code for i in validate_plan_file(f)] == ["E001"]


def test_e001_non_mapping(tmp_path: Path) -> None:
    f = tmp_path / "a.yaml"
    f.write_text("- 1\n- 2\n")
    assert [i.code for i in validate_plan_file(f)] == ["E001"]


def test_file_roundtrip(tmp_path: Path) -> None:
    import yaml

    f = tmp_path / "a.yaml"
    f.write_text(yaml.safe_dump(plan()))
    assert validate_plan_file(f) == []


def test_e002_schema_error() -> None:
    d = plan()
    d["events"][0]["setting"] = "bogus"
    assert codes(d) == [("E002", "/events/0/setting")]


def test_e003_spec_version() -> None:
    d = plan()
    d["spec_version"] = "9.9.0"
    result = issues_for(d)
    assert [i.code for i in result] == ["E003"]
    assert "migrate" in result[0].message


def test_e003_patch_difference_ok() -> None:
    d = plan()
    d["spec_version"] = "0.1.7"
    assert issues_for(d) == []


def test_e101() -> None:
    d = plan()
    d["events"][0]["blocks"] = ["b1", "nope"]
    assert codes(d) == [("E101", "/events/0/blocks/1")]


def test_e102() -> None:
    d = plan()
    d["events"][0]["tools"].append("nope")
    assert codes(d) == [("E102", "/events/0/tools/1")]


def test_e103() -> None:
    d = plan()
    d["blocks"][0]["characteristics"].append("nope")
    assert codes(d) == [("E103", "/blocks/0/characteristics/1")]


def test_e104_missing_and_blank() -> None:
    d = plan()
    d["goals"] = {"q2": "   "}
    assert codes(d) == [("E104", "/goals/q1"), ("E104", "/goals/q2")]


def test_e105_duplicates() -> None:
    d = plan()
    d["blocks"][0]["measures"].append(copy.deepcopy(d["blocks"][0]["measures"][0]))
    assert codes(d) == [("E105", "/blocks/0/measures/1/id")]
    d = plan()
    d["interrogation"].append({"id": "q1", "question": "again"})
    assert codes(d) == [("E105", "/interrogation/1/id")]
    d = plan()
    d["characteristics"].append({"id": "safe", "kind": "trustworthiness"})
    assert codes(d) == [("E105", "/characteristics/1/id")]


def test_e105_blocks_events_tools() -> None:
    d = plan()
    d["blocks"].append(copy.deepcopy(d["blocks"][0]))
    d["events"].append(copy.deepcopy(d["events"][0]))
    d["toolbox"].append(copy.deepcopy(d["toolbox"][0]))
    found = codes(d)
    assert ("E105", "/blocks/1/id") in found
    assert ("E105", "/events/1/id") in found
    assert ("E105", "/toolbox/1/id") in found


def test_e106() -> None:
    d = plan()
    d["toolbox"][0]["adapter"]["map"]["other"] = "nope"
    assert codes(d) == [("E106", "/toolbox/0/adapter/map/other")]


def test_e107() -> None:
    d = plan()
    d["events"][0]["blocks"] = []
    assert codes(d) == [("E107", "/blocks/0")]


def test_e108() -> None:
    d = plan()
    d["events"][0]["tools"] = []
    assert ("E108", "/events/0/tools") in codes(d)


def test_e109() -> None:
    d = plan()
    d["characteristics"][0]["id"] = "spicy"
    d["blocks"][0]["characteristics"] = ["spicy"]
    assert codes(d) == [("E109", "/characteristics/0/id")]


def test_w201() -> None:
    d = plan()
    d["interrogation"] = []
    result = issues_for(d)
    assert [(i.code, i.severity) for i in result] == [("W201", "warning")]


def test_w202() -> None:
    d = plan()
    d["toolbox"].append({"id": "t2", "kind": "questionnaire", "ref": {"name": "y"}})
    assert codes(d) == [("W202", "/toolbox/1")]


def test_deterministic_order() -> None:
    d = plan()
    d["goals"] = {}
    d["interrogation"] = []
    d["events"][0]["blocks"] = ["z", "b1"]
    result = issues_for(d)
    assert result == sorted(result, key=lambda i: (i.path, i.code, i.message))
    assert result == issues_for(copy.deepcopy(d))


def test_catalog_covers_all_codes_with_hints() -> None:
    from tevv_athlon.validate import ISSUE_CATALOG

    assert set(ISSUE_CATALOG) == set(ISSUE_CODES)
    for code, info in ISSUE_CATALOG.items():
        assert info.hint.strip()
        assert ISSUE_CODES[code] == info.title


def test_e002_unknown_field_mentions_extensions() -> None:
    data = plan()
    data["bogus"] = 1
    issues = [i for i in validate_plan_data(data) if i.code == "E002"]
    assert [i.path for i in issues] == ["/bogus"]
    assert "'bogus'" in issues[0].message
    assert "extensions" in issues[0].message
