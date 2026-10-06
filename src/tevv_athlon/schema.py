"""Generate the published JSON Schemas from the Pydantic models."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from tevv_athlon.model import Athlon, EvidenceRecord, Review

__all__ = [
    "JSON_SCHEMA_DIALECT",
    "SCHEMA_BASE_URL",
    "build_schemas",
    "check",
    "export",
    "render",
]

SCHEMA_BASE_URL = "https://neems.github.io/athlon-schema/schema/0.1/"
"""Versioned base URL for the published schemas; each ``$id`` is ``<base><name>.schema.json``."""

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

_MODELS: dict[str, tuple[type[BaseModel], str]] = {
    "athlon": (Athlon, "TEVV-Athlon plan (athlon.yaml)"),
    "evidence": (EvidenceRecord, "TEVV-Athlon evidence record (evidence/*.jsonl line)"),
    "review": (Review, "TEVV-Athlon review (review.yaml)"),
}


def build_schemas() -> dict[str, dict[str, Any]]:
    """Return the JSON Schema for each spec document, keyed by name."""
    schemas: dict[str, dict[str, Any]] = {}
    for name, (model, title) in _MODELS.items():
        schema = model.model_json_schema()
        schema["$schema"] = JSON_SCHEMA_DIALECT
        schema["$id"] = f"{SCHEMA_BASE_URL}{name}.schema.json"
        schema["title"] = title
        schemas[name] = schema
    return schemas


def render() -> dict[str, str]:
    """Return ``{file name: byte-stable JSON text}`` for every schema."""
    return {
        f"{name}.schema.json": json.dumps(schema, sort_keys=True, indent=2, ensure_ascii=False)
        + "\n"
        for name, schema in build_schemas().items()
    }


def check(out_dir: Path) -> list[Path]:
    """Return the schema files under ``out_dir`` that are missing or out of date."""
    stale: list[Path] = []
    for filename, text in render().items():
        target = out_dir / filename
        if not target.is_file() or target.read_text(encoding="utf-8") != text:
            stale.append(target)
    return stale


def export(out_dir: Path) -> list[Path]:
    """Write every ``<name>.schema.json`` into ``out_dir`` and return the written paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, text in render().items():
        target = out_dir / filename
        with target.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        written.append(target)
    return written
