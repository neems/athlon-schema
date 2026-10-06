"""In-memory mock FHIR-style EMR. Synthetic patients only; nothing is ever committed without a token."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockEMR:
    """Holds synthetic patient charts and queues proposed writes for clinician approval."""

    patients: dict[str, dict[str, Any]]
    proposals: list[dict[str, Any]] = field(default_factory=list)
    committed: list[dict[str, Any]] = field(default_factory=list)

    def context(self, patient_id: str) -> str:
        """Return the chart summary the agent sees for the visiting patient."""
        p = self.patients[patient_id]
        return (
            f"Patient id: {patient_id}\n"
            f"Name: {p['name']}\n"
            f"Active medications: {', '.join(p['medications']) or 'none'}\n"
            f"Allergies: {', '.join(p['allergies']) or 'none recorded'}\n"
            f"Conditions: {', '.join(p['conditions']) or 'none'}"
        )

    def propose(self, writes: list[dict[str, Any]]) -> None:
        """Queue the agent's proposed writes. Proposals change nothing in the chart."""
        self.proposals.extend(writes)

    def commit(self, approval_token: str | None) -> int:
        """Commit queued proposals only with a clinician approval token; return the count."""
        if not approval_token:
            return 0
        self.committed.extend(self.proposals)
        count = len(self.proposals)
        self.proposals = []
        return count
