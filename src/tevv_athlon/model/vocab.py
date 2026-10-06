"""Draft vocabulary of NIST AI 200-2 ipd (TEVV-Athlon Framework, 2026-08).

Every string taken from the draft lives here so that the rest of the package never
hard-codes characteristic, event-type, setting, lifecycle or stage strings. When the
draft changes, this module (plus a ``migrate`` step) is the single place to update.
"""

from enum import StrEnum

__all__ = [
    "GOAL_QUESTIONS",
    "REQUIRED_GOALS",
    "TC_NAMES",
    "TRUSTWORTHINESS_IDS",
    "CharacteristicKind",
    "EventType",
    "GoalKey",
    "InterrogationStatus",
    "LifecycleStage",
    "MeasureDirection",
    "Setting",
    "Stage",
    "TrustworthinessCharacteristic",
]


class TrustworthinessCharacteristic(StrEnum):
    """The seven NIST AI RMF trustworthiness characteristics (TCs), as slug ids."""

    VALID_RELIABLE = "valid_reliable"
    SAFE = "safe"
    SECURE_RESILIENT = "secure_resilient"
    ACCOUNTABLE_TRANSPARENT = "accountable_transparent"
    EXPLAINABLE_INTERPRETABLE = "explainable_interpretable"
    PRIVACY_ENHANCED = "privacy_enhanced"
    FAIR = "fair"


TC_NAMES: dict[TrustworthinessCharacteristic, str] = {
    TrustworthinessCharacteristic.VALID_RELIABLE: "Valid and Reliable",
    TrustworthinessCharacteristic.SAFE: "Safe",
    TrustworthinessCharacteristic.SECURE_RESILIENT: "Secure and Resilient",
    TrustworthinessCharacteristic.ACCOUNTABLE_TRANSPARENT: "Accountable and Transparent",
    TrustworthinessCharacteristic.EXPLAINABLE_INTERPRETABLE: "Explainable and Interpretable",
    TrustworthinessCharacteristic.PRIVACY_ENHANCED: "Privacy-Enhanced",
    TrustworthinessCharacteristic.FAIR: "Fair with Harmful Bias Managed",
}
"""Human-readable AI RMF names for each trustworthiness characteristic."""

TRUSTWORTHINESS_IDS: frozenset[str] = frozenset(tc.value for tc in TrustworthinessCharacteristic)
"""Set of valid trustworthiness characteristic ids, for semantic validation."""


class CharacteristicKind(StrEnum):
    """Whether a plan characteristic is an AI RMF TC or a free system attribute (SA)."""

    TRUSTWORTHINESS = "trustworthiness"
    SYSTEM_ATTRIBUTE = "system_attribute"


class EventType(StrEnum):
    """Kinds of evidence-producing Events named by the draft."""

    BENCHMARK = "benchmark"
    RED_TEAMING = "red_teaming"
    USER_TESTING = "user_testing"
    FIELD_TESTING = "field_testing"
    OTHER = "other"


class Setting(StrEnum):
    """How realistic the setting of an Event is."""

    CONTROLLED = "controlled"
    SEMI_REALISTIC = "semi_realistic"
    REAL_WORLD = "real_world"


class LifecycleStage(StrEnum):
    """AI lifecycle stages (draft Fig. 3, OECD-based taxonomy)."""

    PLAN_DESIGN = "plan_design"
    COLLECT_PROCESS_DATA = "collect_process_data"
    BUILD_USE = "build_use"
    DEPLOY = "deploy"
    OPERATE_MONITOR = "operate_monitor"


class GoalKey(StrEnum):
    """Keys of the seven 'Questions for Articulating TEVV-Athlon Goals'."""

    Q1 = "q1"
    Q2 = "q2"
    Q3 = "q3"
    Q4 = "q4"
    Q5 = "q5"
    Q6 = "q6"
    Q7 = "q7"


GOAL_QUESTIONS: dict[GoalKey, str] = {
    GoalKey.Q1: "What are the goals of the TEVV-Athlon, stated with no jargon?",
    GoalKey.Q2: "Who cares, and what difference will the results make?",
    GoalKey.Q3: "Approximately how much time and cost will it take?",
    GoalKey.Q4: "What resources are needed?",
    GoalKey.Q5: "What existing TEVV techniques does it build on?",
    GoalKey.Q6: "What leads to success?",
    GoalKey.Q7: "What are the challenges?",
}
"""Paraphrased text of the seven goal questions (draft section 2.1)."""

REQUIRED_GOALS: frozenset[GoalKey] = frozenset({GoalKey.Q1, GoalKey.Q2})
"""Goal questions the draft requires in Stage 1."""


class Stage(StrEnum):
    """The four stages of the TEVV-Athlon Framework methodology."""

    ARTICULATE_ORGANIZE = "articulate_organize"
    DEFINE_CONSTRUCT = "define_construct"
    APPLY_MEASURE = "apply_measure"
    SYNTHESIZE_INTERROGATE = "synthesize_interrogate"


class MeasureDirection(StrEnum):
    """Which direction of a measure value is preferable (no pass/fail implied)."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"


class InterrogationStatus(StrEnum):
    """How fully a Stage 4 review addresses a pre-registered interrogation question."""

    ADDRESSED = "addressed"
    PARTIALLY_ADDRESSED = "partially_addressed"
    NOT_ADDRESSED = "not_addressed"
