"""The Pages landing page must link every published schema and keep the required notices."""

from pathlib import Path

from tevv_athlon.model import SPEC_VERSION
from tevv_athlon.schema import build_schemas

INDEX = Path(__file__).resolve().parent.parent / "site" / "index.html"


def test_landing_page_links_every_schema_id() -> None:
    html = INDEX.read_text(encoding="utf-8")
    for name, schema in build_schemas().items():
        assert f'href="{schema["$id"]}"' in html, f"site/index.html does not link the {name} schema"


def test_landing_page_states_spec_version() -> None:
    assert f"Spec version {SPEC_VERSION}" in INDEX.read_text(encoding="utf-8")


def test_landing_page_carries_non_affiliation_notice() -> None:
    assert "Not affiliated with or endorsed by NIST" in INDEX.read_text(encoding="utf-8")


def test_landing_page_is_light_only() -> None:
    html = INDEX.read_text(encoding="utf-8")
    assert '<meta name="color-scheme" content="only light">' in html
    assert "color-scheme: only light" in html
    assert "prefers-color-scheme" not in html
