"""Tests for the Pydantic data models."""

import copy
import json
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from tevv_athlon.model import (
    FRAMEWORK_REF,
    SPEC_VERSION,
    Athlon,
    EvidenceRecord,
    Review,
    vocab,
)
from tevv_athlon.model.vocab import EventType, LifecycleStage, Setting


def minimal_plan() -> dict[str, Any]:
    return {
        "spec_version": SPEC_VERSION,
        "framework_ref": FRAMEWORK_REF,
        "id": "demo",
        "title": "Demo athlon",
        "system": {"name": "Demo bot", "description": "A chatbot."},
        "lifecycle_stage": "build_use",
        "goals": {"q1": "Check it answers safely.", "q2": "Product owners decide launch."},
        "characteristics": [
            {"id": "safe", "kind": "trustworthiness"},
            {"id": "latency", "kind": "system_attribute", "name": "Latency"},
        ],
        "blocks": [
            {
                "id": "violation_frequency",
                "characteristics": ["safe"],
                "definition": "Share of answers that give a prohibited violation.",
                "evidence_required": "Annotated transcripts.",
                "measures": [
                    {
                        "id": "violation_rate",
                        "unit": "proportion",
                        "direction": "lower_is_better",
                        "target": 0.01,
                    }
                ],
            }
        ],
        "events": [
            {
                "id": "red_team",
                "type": "red_teaming",
                "setting": "controlled",
                "blocks": ["violation_frequency"],
                "tools": ["promptfoo"],
                "conditions": {"framing": ["test", "realistic"]},
            }
        ],
        "toolbox": [
            {
                "id": "promptfoo",
                "kind": "eval_harness",
                "ref": {"name": "promptfoo", "url": "https://github.com/promptfoo/promptfoo"},
                "adapter": {"type": "promptfoo", "map": {"violation": "violation_rate"}},
            }
        ],
        "interrogation": [{"id": "eval_awareness", "question": "Does framing change behavior?"}],
    }


def evidence_data() -> dict[str, Any]:
    return {
        "event": "red_team",
        "tool": "promptfoo",
        "block": "violation_frequency",
        "measure": "violation_rate",
        "value": True,
        "subject": {"kind": "episode", "id": "ep-1"},
        "conditions": {"framing": "test"},
        "source": {
            "uri": "out/results.json",
            "sha256": "0" * 64,
            "adapter": "promptfoo",
            "adapter_version": "0.1.0",
        },
        "environment": {"model": "some-llm", "config_hash": "abc"},
        "collected_at": "2026-10-05T12:00:00Z",
    }


def review_data() -> dict[str, Any]:
    return {
        "spec_version": SPEC_VERSION,
        "framework_ref": FRAMEWORK_REF,
        "athlon": "demo",
        "interrogation": [
            {"question": "eval_awareness", "status": "partially_addressed", "response": "Some."}
        ],
        "limitations": ["Synthetic data only."],
        "validity_boundary": "English-language chat in controlled settings.",
    }


def test_minimal_plan_round_trip() -> None:
    plan = Athlon.model_validate(minimal_plan())
    assert plan.lifecycle_stage is LifecycleStage.BUILD_USE
    assert plan.events[0].type is EventType.RED_TEAMING
    assert plan.events[0].setting is Setting.CONTROLLED
    dumped = plan.model_dump(mode="json", exclude_none=True)
    again = Athlon.model_validate(dumped)
    assert again == plan
    assert Athlon.model_validate_json(plan.model_dump_json()) == plan


def test_goals_optional_at_model_level() -> None:
    data = minimal_plan()
    data["goals"] = {}
    assert Athlon.model_validate(data).goals.q1 is None


@pytest.mark.parametrize(
    "path",
    [
        (),
        ("system",),
        ("goals",),
        ("characteristics", 0),
        ("blocks", 0),
        ("blocks", 0, "measures", 0),
        ("events", 0),
        ("toolbox", 0),
        ("toolbox", 0, "ref"),
        ("toolbox", 0, "adapter"),
        ("interrogation", 0),
    ],
)
def test_unknown_fields_rejected(path: tuple[str | int, ...]) -> None:
    data = minimal_plan()
    target: Any = data
    for key in path:
        target = target[key]
    target["score"] = 1
    with pytest.raises(ValidationError) as exc:
        Athlon.model_validate(data)
    assert exc.value.errors()[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize(
    "path",
    [(), ("blocks", 0), ("events", 0), ("toolbox", 0), ("blocks", 0, "measures", 0)],
)
def test_extensions_accepted(path: tuple[str | int, ...]) -> None:
    data = minimal_plan()
    target: Any = data
    for key in path:
        target = target[key]
    target["extensions"] = {"x-status": "declared_not_run", "nested": {"a": [1, 2]}}
    plan = Athlon.model_validate(data)
    obj: Any = plan
    for key in path:
        obj = obj[key] if isinstance(key, int) else getattr(obj, key)
    assert obj.extensions == {"x-status": "declared_not_run", "nested": {"a": [1, 2]}}


def test_invalid_vocab_rejected() -> None:
    for field, bad in (("type", "hackathon"), ("setting", "lab")):
        data = minimal_plan()
        data["events"][0][field] = bad
        with pytest.raises(ValidationError):
            Athlon.model_validate(data)
    data = minimal_plan()
    data["lifecycle_stage"] = "retire"
    with pytest.raises(ValidationError):
        Athlon.model_validate(data)


def test_evidence_record_parsing() -> None:
    record = EvidenceRecord.model_validate(evidence_data())
    assert record.value is True
    assert record.collected_at.year == 2026
    assert EvidenceRecord.model_validate_json(record.model_dump_json()) == record
    for value in (0.25, 3, "yes"):
        data = evidence_data()
        data["value"] = value
        assert EvidenceRecord.model_validate(data).value == value
    bad = evidence_data()
    bad["source"]["signature"] = "x"
    with pytest.raises(ValidationError):
        EvidenceRecord.model_validate(bad)


def test_review_parsing() -> None:
    review = Review.model_validate(review_data())
    assert review.interrogation[0].status == vocab.InterrogationStatus.PARTIALLY_ADDRESSED
    assert Review.model_validate_json(review.model_dump_json()) == review
    bad = review_data()
    bad["interrogation"][0]["status"] = "passed"
    with pytest.raises(ValidationError):
        Review.model_validate(bad)
    bad = review_data()
    bad["verdict"] = "pass"
    with pytest.raises(ValidationError):
        Review.model_validate(bad)


@pytest.mark.parametrize("model", [Athlon, EvidenceRecord, Review])
def test_json_schema_generation(model: type[BaseModel]) -> None:
    schema = model.model_json_schema()
    text = json.dumps(schema)
    assert schema["additionalProperties"] is False
    for banned in ('"score"', '"pass"', '"fail"', '"composite"', '"passed"', '"verdict"'):
        assert banned not in text
    assert '"description"' in text


def test_vocabulary_contents() -> None:
    assert len(vocab.TrustworthinessCharacteristic) == 7
    assert vocab.TRUSTWORTHINESS_IDS == {
        "valid_reliable",
        "safe",
        "secure_resilient",
        "accountable_transparent",
        "explainable_interpretable",
        "privacy_enhanced",
        "fair",
    }
    assert [s.value for s in vocab.LifecycleStage] == [
        "plan_design",
        "collect_process_data",
        "build_use",
        "deploy",
        "operate_monitor",
    ]
    assert [k.value for k in vocab.GoalKey] == [f"q{i}" for i in range(1, 8)]
    assert len(vocab.Stage) == 4
    assert set(vocab.GOAL_QUESTIONS) == set(vocab.GoalKey)


def test_input_not_mutated() -> None:
    data = minimal_plan()
    before = copy.deepcopy(data)
    Athlon.model_validate(data)
    assert data == before
