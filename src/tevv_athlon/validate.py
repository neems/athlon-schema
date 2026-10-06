"""Basic validator for Athlon plans: schema checks plus semantic cross-reference checks."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import ValidationError

from tevv_athlon.model import SPEC_VERSION, Athlon
from tevv_athlon.model.vocab import (
    REQUIRED_GOALS,
    TRUSTWORTHINESS_IDS,
    CharacteristicKind,
)

__all__ = [
    "ISSUE_CATALOG",
    "ISSUE_CODES",
    "Issue",
    "IssueInfo",
    "validate_plan_data",
    "validate_plan_file",
]


@dataclass(frozen=True)
class IssueInfo:
    """Machine-readable explanation of one issue code."""

    title: str
    hint: str


ISSUE_CATALOG: dict[str, IssueInfo] = {
    "E001": IssueInfo(
        "File is not parseable YAML or top level is not a mapping",
        "Fix the YAML syntax and make sure the file's top level is a mapping of plan fields.",
    ),
    "E002": IssueInfo(
        "Schema violation",
        "Read the path and message, then correct that field's type or value. "
        "Put data beyond the spec under 'extensions'.",
    ),
    "E003": IssueInfo(
        "Unsupported spec_version",
        f"Set spec_version to {SPEC_VERSION}, or migrate the plan to that version.",
    ),
    "E101": IssueInfo(
        "Unknown block reference in event",
        "Change the event's blocks entry to the id of a declared block, or add that block.",
    ),
    "E102": IssueInfo(
        "Unknown tool reference in event",
        "Change the event's tools entry to the id of a toolbox tool, or add that tool.",
    ),
    "E103": IssueInfo(
        "Unknown characteristic reference in block",
        "Change the block's characteristics entry to a declared characteristic id, "
        "or declare that characteristic.",
    ),
    "E104": IssueInfo(
        "Goal q1 or q2 missing or blank",
        "Give goals.q1 and goals.q2 non-blank text.",
    ),
    "E105": IssueInfo(
        "Duplicate id",
        "Rename one of the entries so every id in that list is unique.",
    ),
    "E106": IssueInfo(
        "Adapter map target is not a measure of any block",
        "Change the adapter map value to the id of a measure declared under "
        "blocks[].measures, or add that measure.",
    ),
    "E107": IssueInfo(
        "Block not referenced by any event",
        "Reference the block from an event's blocks list, or remove the block.",
    ),
    "E108": IssueInfo(
        "Event has no tools",
        "Add at least one toolbox tool id to the event's tools list.",
    ),
    "E109": IssueInfo(
        "Unknown trustworthiness characteristic id",
        "Use one of the known trustworthiness characteristic ids from the spec vocabulary.",
    ),
    "W201": IssueInfo(
        "Plan has no interrogation questions",
        "Add questions under 'interrogation' to probe the plan's assumptions.",
    ),
    "W202": IssueInfo(
        "Tool not used by any event",
        "Reference the tool from an event's tools list, or remove it from the toolbox.",
    ),
}
"""Every issue code with its title and fix hint."""

ISSUE_CODES: dict[str, str] = {code: info.title for code, info in ISSUE_CATALOG.items()}
"""Every issue code with a short title."""


@dataclass(frozen=True)
class Issue:
    """One validation finding. ``path`` is a JSON pointer into the plan document."""

    path: str
    code: str
    severity: Literal["error", "warning"]
    message: str


def _pointer(parts: Iterable[str | int]) -> str:
    return "".join("/" + str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def _issue(path: str, code: str, message: str) -> Issue:
    severity: Literal["error", "warning"] = "warning" if code.startswith("W") else "error"
    return Issue(path, code, severity, message)


def _schema_message(err_type: str, loc: tuple[str | int, ...], msg: str) -> str:
    if err_type == "extra_forbidden" and loc:
        return (
            f"Unknown field '{loc[-1]}' is not part of the spec; "
            "data beyond the spec belongs under 'extensions'"
        )
    return msg


def _major_minor(version: str) -> tuple[str, ...]:
    return tuple(version.split(".")[:2])


def _duplicates(ids: list[str], base: str) -> list[Issue]:
    seen: set[str] = set()
    out: list[Issue] = []
    for i, ident in enumerate(ids):
        if ident in seen:
            out.append(_issue(f"{base}/{i}/id", "E105", f"Duplicate id '{ident}'"))
        seen.add(ident)
    return out


def _semantic(plan: Athlon) -> list[Issue]:
    issues: list[Issue] = []

    for key in sorted(REQUIRED_GOALS):
        value = getattr(plan.goals, key.value)
        if value is None or not value.strip():
            issues.append(
                _issue(f"/goals/{key.value}", "E104", f"Goal {key.value} is missing or blank")
            )

    issues += _duplicates([b.id for b in plan.blocks], "/blocks")
    issues += _duplicates([e.id for e in plan.events], "/events")
    issues += _duplicates([t.id for t in plan.toolbox], "/toolbox")
    issues += _duplicates([c.id for c in plan.characteristics], "/characteristics")
    issues += _duplicates([q.id for q in plan.interrogation], "/interrogation")
    for bi, block in enumerate(plan.blocks):
        issues += _duplicates([m.id for m in block.measures], f"/blocks/{bi}/measures")

    block_ids = {b.id for b in plan.blocks}
    tool_ids = {t.id for t in plan.toolbox}
    char_ids = {c.id for c in plan.characteristics}
    measure_ids = {m.id for b in plan.blocks for m in b.measures}

    for bi, block in enumerate(plan.blocks):
        for ci, ref in enumerate(block.characteristics):
            if ref not in char_ids:
                issues.append(
                    _issue(
                        f"/blocks/{bi}/characteristics/{ci}",
                        "E103",
                        f"Unknown characteristic '{ref}'",
                    )
                )

    used_blocks: set[str] = set()
    used_tools: set[str] = set()
    for ei, event in enumerate(plan.events):
        for bi, ref in enumerate(event.blocks):
            used_blocks.add(ref)
            if ref not in block_ids:
                issues.append(_issue(f"/events/{ei}/blocks/{bi}", "E101", f"Unknown block '{ref}'"))
        for ti, ref in enumerate(event.tools):
            used_tools.add(ref)
            if ref not in tool_ids:
                issues.append(_issue(f"/events/{ei}/tools/{ti}", "E102", f"Unknown tool '{ref}'"))
        if not event.tools:
            issues.append(_issue(f"/events/{ei}/tools", "E108", f"Event '{event.id}' has no tools"))

    for ti, tool in enumerate(plan.toolbox):
        if tool.adapter is not None:
            for src, target in tool.adapter.map.items():
                if target not in measure_ids:
                    issues.append(
                        _issue(
                            _pointer(["toolbox", ti, "adapter", "map", src]),
                            "E106",
                            f"Adapter target '{target}' is not a measure of any block",
                        )
                    )
        if tool.id not in used_tools:
            issues.append(
                _issue(f"/toolbox/{ti}", "W202", f"Tool '{tool.id}' is not used by any event")
            )

    for bi, block in enumerate(plan.blocks):
        if block.id not in used_blocks:
            issues.append(
                _issue(
                    f"/blocks/{bi}", "E107", f"Block '{block.id}' is not referenced by any event"
                )
            )

    for ci, char in enumerate(plan.characteristics):
        if char.kind == CharacteristicKind.TRUSTWORTHINESS and char.id not in TRUSTWORTHINESS_IDS:
            issues.append(
                _issue(
                    f"/characteristics/{ci}/id",
                    "E109",
                    f"'{char.id}' is not a trustworthiness characteristic id",
                )
            )

    if not plan.interrogation:
        issues.append(_issue("/interrogation", "W201", "Plan has no interrogation questions"))
    return issues


def validate_plan_data(data: dict[str, Any]) -> list[Issue]:
    """Validate an already-loaded plan document; issues are sorted by path then code."""
    version = data.get("spec_version")
    if isinstance(version, str) and _major_minor(version) != _major_minor(SPEC_VERSION):
        return [
            _issue(
                "/spec_version",
                "E003",
                f"spec_version '{version}' is not supported (expected {SPEC_VERSION}); "
                "a future `tevv-athlon migrate` will handle this",
            )
        ]
    try:
        plan = Athlon.model_validate(data)
    except ValidationError as exc:
        issues = [
            _issue(_pointer(e["loc"]), "E002", _schema_message(e["type"], e["loc"], e["msg"]))
            for e in exc.errors()
        ]
        return sorted(issues, key=lambda i: (i.path, i.code, i.message))
    return sorted(_semantic(plan), key=lambda i: (i.path, i.code, i.message))


def validate_plan_file(path: Path) -> list[Issue]:
    """Load a plan with ``yaml.safe_load`` and validate it."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        return [_issue("", "E001", f"Cannot parse YAML: {exc}")]
    if not isinstance(data, dict):
        return [_issue("", "E001", "Top level of the plan must be a mapping")]
    return validate_plan_data(data)
