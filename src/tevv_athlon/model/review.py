"""The Stage 4 review (``review.yaml``): authored by humans after testing."""

from pydantic import Field

from tevv_athlon.model.plan import AthlonBaseModel
from tevv_athlon.model.vocab import InterrogationStatus

__all__ = ["InterrogationResponse", "Review"]


class InterrogationResponse(AthlonBaseModel):
    """The answer to one pre-registered interrogation question."""

    question: str = Field(description="Id of the interrogation question in the plan.")
    status: InterrogationStatus = Field(description="How fully the question is addressed.")
    response: str = Field(description="The answer, with reference to the evidence.")


class Review(AthlonBaseModel):
    """Human Stage 4 synthesis: interrogation answers, limitations and validity boundary."""

    spec_version: str = Field(description="Version (semver) of the tevv-athlon spec used.")
    framework_ref: str = Field(description="Framework edition the review follows.")
    athlon: str = Field(description="Id of the Athlon plan being reviewed.")
    interrogation: list[InterrogationResponse] = Field(
        default_factory=list, description="Responses to pre-registered interrogation questions."
    )
    limitations: list[str] = Field(
        default_factory=list, description="Known limitations of the evaluation."
    )
    validity_boundary: str = Field(
        description="Conditions under which the results are expected to hold."
    )
