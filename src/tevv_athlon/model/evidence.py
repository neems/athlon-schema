"""Evidence records (``evidence/*.jsonl``): one observation plus provenance."""

from datetime import datetime

from pydantic import Field

from tevv_athlon.model.plan import AthlonBaseModel

__all__ = ["Environment", "EvidenceRecord", "Source", "Subject"]


class Subject(AthlonBaseModel):
    """What was observed, e.g. an episode for an agentic system."""

    kind: str = Field(description="Kind of subject, e.g. 'episode', 'test_case', 'participant'.")
    id: str = Field(description="Identifier of the subject within its source.")


class Source(AthlonBaseModel):
    """Provenance of the raw data a record was derived from."""

    uri: str = Field(description="Location of the raw source file.")
    sha256: str = Field(description="SHA-256 hex digest of the raw source file.")
    adapter: str = Field(description="Adapter type that produced the record.")
    adapter_version: str = Field(description="Version of the adapter.")


class Environment(AthlonBaseModel):
    """The configuration under which the observation was made."""

    model: str | None = Field(default=None, description="Underlying model, if any.")
    version: str | None = Field(default=None, description="Version of the system or model.")
    config_hash: str | None = Field(default=None, description="Hash of the run configuration.")


class EvidenceRecord(AthlonBaseModel):
    """A single observation of one measure, tied to an Event, Tool and Block."""

    event: str = Field(description="Id of the Event that produced the observation.")
    tool: str = Field(description="Id of the Tool used.")
    block: str = Field(description="Id of the Block the observation is evidence for.")
    measure: str = Field(description="Id of the measure within the Block.")
    value: bool | int | float | str = Field(description="Observed value.")
    subject: Subject = Field(description="What was observed.")
    conditions: dict[str, str] = Field(
        default_factory=dict,
        description="Level of each Event condition factor under which this was observed.",
    )
    source: Source = Field(description="Provenance of the raw data.")
    environment: Environment = Field(default_factory=Environment, description="Run configuration.")
    collected_at: datetime = Field(description="When the observation was collected.")
