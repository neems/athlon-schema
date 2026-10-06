"""The Athlon plan (``athlon.yaml``): Stages 1 to 3, authored before testing."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from tevv_athlon.model.vocab import (
    CharacteristicKind,
    EventType,
    LifecycleStage,
    MeasureDirection,
    Setting,
)

__all__ = [
    "Adapter",
    "Athlon",
    "AthlonBaseModel",
    "Block",
    "Characteristic",
    "Event",
    "Goals",
    "InterrogationQuestion",
    "Measure",
    "System",
    "Tool",
    "ToolRef",
]


class AthlonBaseModel(BaseModel):
    """Base for every spec object: unknown fields are rejected, except ``extensions``."""

    model_config = ConfigDict(extra="forbid")

    extensions: dict[str, Any] | None = Field(
        default=None,
        description="Free-form data beyond the NIST AI 200-2 ipd draft. "
        "The only place where unspecified fields are allowed.",
    )


class System(AthlonBaseModel):
    """The AI system under evaluation."""

    name: str = Field(description="Name of the AI system under evaluation.")
    description: str = Field(description="Plain-language description of the system.")
    version: str | None = Field(default=None, description="Version of the system evaluated.")


class Goals(AthlonBaseModel):
    """Answers to the seven 'Questions for Articulating TEVV-Athlon Goals' (draft 2.1).

    All are optional here; the validator requires q1 and q2.
    """

    q1: str | None = Field(default=None, description="Q1: the goals, stated with no jargon.")
    q2: str | None = Field(
        default=None, description="Q2: who cares, and what difference the results make."
    )
    q3: str | None = Field(default=None, description="Q3: approximate time and cost.")
    q4: str | None = Field(default=None, description="Q4: resources needed.")
    q5: str | None = Field(default=None, description="Q5: existing TEVV techniques built on.")
    q6: str | None = Field(
        default=None, description="Q6: what leads to success (may inform measure targets)."
    )
    q7: str | None = Field(default=None, description="Q7: anticipated challenges.")


class Characteristic(AthlonBaseModel):
    """A system attribute (SA) or trustworthiness characteristic (TC) being evaluated."""

    id: str = Field(
        description="Identifier. For an AI RMF trustworthiness characteristic it must be "
        "one of the vocabulary TC slugs (checked by the validator); for a system attribute "
        "it is free."
    )
    kind: CharacteristicKind = Field(
        description="Whether this is an AI RMF trustworthiness characteristic or a "
        "system attribute."
    )
    name: str | None = Field(default=None, description="Human-readable name.")
    description: str | None = Field(default=None, description="What the characteristic means here.")


class Measure(AthlonBaseModel):
    """A quantity reported for a Block. Targets are optional and never a pass/fail."""

    id: str = Field(description="Identifier, unique within its Block.")
    unit: str = Field(description="Unit of the measure, e.g. 'proportion' or 'seconds'.")
    direction: MeasureDirection = Field(description="Which direction of the value is preferable.")
    target: float | None = Field(
        default=None,
        description="Optional reference value derived from goal Q6, shown alongside "
        "the estimate. It is not a pass/fail threshold.",
    )


class Block(AthlonBaseModel):
    """A Metrology Block: a key concept or metric the evaluation aims to assess."""

    id: str = Field(description="Block identifier, unique within the plan.")
    characteristics: list[str] = Field(
        description="Ids of the characteristics this Block provides evidence for."
    )
    definition: str = Field(description="Precise definition of the concept being measured.")
    evidence_required: str = Field(description="Definition of the evidence the Block needs.")
    measures: list[Measure] = Field(description="Measures reported for this Block.")


class Event(AthlonBaseModel):
    """An activity that produces evidence for one or more Blocks."""

    id: str = Field(description="Event identifier, unique within the plan.")
    type: EventType = Field(description="Kind of Event.")
    setting: Setting = Field(description="How realistic the Event setting is.")
    blocks: list[str] = Field(description="Ids of the Blocks this Event produces evidence for.")
    tools: list[str] = Field(description="Ids of Toolbox tools used in this Event.")
    conditions: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Experimental factors and their levels, e.g. {framing: [test, realistic]}. "
        "Evidence records tag observations with one level per factor.",
    )
    description: str | None = Field(default=None, description="What the Event involves.")


class ToolRef(AthlonBaseModel):
    """Reference to the external method or instrument a Tool uses."""

    name: str = Field(description="Name of the tool, instrument or method.")
    version: str | None = Field(default=None, description="Version of the tool.")
    url: str | None = Field(default=None, description="Where the tool can be found.")


class Adapter(AthlonBaseModel):
    """How a Tool's raw output is turned into evidence records."""

    type: str = Field(description="Adapter type, e.g. 'promptfoo' or 'tabular'.")
    map: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from source metric name to the measure id it reports.",
    )


class Tool(AthlonBaseModel):
    """A Toolbox entry: a method or instrument used to elicit, collect or analyze data."""

    id: str = Field(description="Tool identifier, unique within the Toolbox.")
    kind: str = Field(
        description="Kind of tool, e.g. 'eval_harness', 'questionnaire', 'annotation_schema'."
    )
    ref: ToolRef = Field(description="Reference to the external tool or method.")
    adapter: Adapter | None = Field(
        default=None, description="Adapter that normalizes this tool's output into evidence."
    )


class InterrogationQuestion(AthlonBaseModel):
    """A pre-registered Stage 4 question about measurement validity."""

    id: str = Field(description="Question identifier, unique within the plan.")
    question: str = Field(description="The question to answer after testing.")
    rationale: str | None = Field(default=None, description="Why the question matters.")


class Athlon(AthlonBaseModel):
    """A TEVV-Athlon plan covering Stages 1 to 3 of NIST AI 200-2 ipd."""

    spec_version: str = Field(description="Version (semver) of the tevv-athlon spec used.")
    framework_ref: str = Field(
        description="Framework edition the plan follows, e.g. 'NIST AI 200-2 ipd (2026-08)'."
    )
    id: str = Field(description="Plan identifier.")
    title: str = Field(description="Human-readable plan title.")
    system: System = Field(description="The AI system under evaluation.")
    lifecycle_stage: LifecycleStage = Field(
        description="AI lifecycle stage the evaluation targets (draft Fig. 3)."
    )
    goals: Goals = Field(description="Answers to the seven goal questions.")
    characteristics: list[Characteristic] = Field(
        default_factory=list, description="Characteristics (SA/TC) being evaluated."
    )
    blocks: list[Block] = Field(default_factory=list, description="Metrology Blocks.")
    events: list[Event] = Field(default_factory=list, description="Evidence-producing Events.")
    toolbox: list[Tool] = Field(default_factory=list, description="Tools used by the Events.")
    interrogation: list[InterrogationQuestion] = Field(
        default_factory=list,
        description="Validity questions pre-registered before testing, answered in the review.",
    )
