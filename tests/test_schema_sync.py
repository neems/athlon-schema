"""The committed spec/schema files must match what the models generate, byte for byte."""

import json
from pathlib import Path

from tevv_athlon.schema import JSON_SCHEMA_DIALECT, build_schemas, render

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "spec" / "schema"


def test_committed_schemas_match_models() -> None:
    rendered = render()
    assert sorted(rendered) == ["athlon.schema.json", "evidence.schema.json", "review.schema.json"]
    for filename, text in rendered.items():
        committed = (SCHEMA_DIR / filename).read_bytes()
        assert committed == text.encode("utf-8"), (
            f"{filename} is stale; run `uv run tevv-athlon schema export`"
        )


def test_build_schemas_matches_rendered_text() -> None:
    for name, schema in build_schemas().items():
        on_disk = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert on_disk == schema


def test_schema_metadata() -> None:
    for name, schema in build_schemas().items():
        assert schema["$schema"] == JSON_SCHEMA_DIALECT
        assert schema["$id"].endswith(f"/0.1/{name}.schema.json")
        assert schema["title"]
