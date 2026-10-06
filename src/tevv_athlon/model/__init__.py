"""Pydantic v2 models: the single source of truth for the tevv-athlon spec."""

from tevv_athlon.model.evidence import Environment, EvidenceRecord, Source, Subject
from tevv_athlon.model.plan import (
    Adapter,
    Athlon,
    AthlonBaseModel,
    Block,
    Characteristic,
    Event,
    Goals,
    InterrogationQuestion,
    Measure,
    System,
    Tool,
    ToolRef,
)
from tevv_athlon.model.review import InterrogationResponse, Review

SPEC_VERSION = "0.1.0"
"""Version of the tevv-athlon spec implemented by these models."""

FRAMEWORK_REF = "NIST AI 200-2 ipd (2026-08)"
"""Edition of the NIST framework the spec follows."""

__all__ = [
    "FRAMEWORK_REF",
    "SPEC_VERSION",
    "Adapter",
    "Athlon",
    "AthlonBaseModel",
    "Block",
    "Characteristic",
    "Environment",
    "Event",
    "EvidenceRecord",
    "Goals",
    "InterrogationQuestion",
    "InterrogationResponse",
    "Measure",
    "Review",
    "Source",
    "Subject",
    "System",
    "Tool",
    "ToolRef",
]
