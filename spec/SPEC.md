# TEVV-Athlon file format specification

Version 0.1.0 (draft). Framework reference: NIST AI 200-2 ipd (2026-08).

This is an independent, community specification. It is not affiliated with or endorsed by NIST.
The normative machine-readable definitions are the JSON Schemas in `spec/schema/`, generated from
the Pydantic models in `src/tevv_athlon/model/`. This document is the human-readable companion.

## 1. Status and versioning policy

- While NIST AI 200-2 is a draft, this spec is 0.x and may change between minor versions.
- Version 1.0 will be aligned with the NIST final publication.
- Every schema has a versioned `$id` URL of the form
  `https://neems.github.io/athlon-schema/schema/0.1/<name>.schema.json`, where it is also published.
- At the first breaking change a `tevv-athlon migrate` command will be provided. Until then the
  validator rejects any `spec_version` whose major.minor differs from the supported one (E003).

## 2. The four stages and four files

| Stage | TEVV-Athlon stage | File | Owner |
|---|---|---|---|
| 1 | Articulate and organize | `athlon.yaml` (goals, characteristics) | Evaluation lead (human) |
| 2 | Define and construct | `athlon.yaml` (blocks, measures) | Evaluation lead / metrologist (human) |
| 3 | Apply and measure | `athlon.yaml` (events, toolbox) and `evidence/*.jsonl` | Plan by humans; evidence by tools via adapters |
| 4 | Synthesize and interrogate | `review.yaml`, then `report.json` / `report.html` | Review by humans; report to be generated (planned) |

`athlon.yaml` is authored before testing. `evidence/*.jsonl` holds one JSON object per line. 
`review.yaml` is authored after testing. `report.json` and `report.html` are planned and will be
generated (section 10).

## 3. Field reference

Every object rejects unknown fields, except through `extensions` (section 5).
"Req" means required by the schema. Types are JSON types.

### 3.1 Athlon (`athlon.yaml`)

| Field | Type | Req | Description |
|---|---|---|---|
| `spec_version` | string | yes | Spec semver used. |
| `framework_ref` | string | yes | Framework edition followed. |
| `id` | string | yes | Plan identifier. |
| `title` | string | yes | Plan title. |
| `system` | System | yes | System under evaluation. |
| `lifecycle_stage` | LifecycleStage | yes | Lifecycle stage targeted. |
| `goals` | Goals | yes | Answers to the seven goal questions. |
| `characteristics` | Characteristic[] | no | Characteristics evaluated. |
| `blocks` | Block[] | no | Metrology Blocks. |
| `events` | Event[] | no | Evidence-producing Events. |
| `toolbox` | Tool[] | no | Tools used by Events. |
| `interrogation` | InterrogationQuestion[] | no | Validity questions pre-registered before testing. |
| `extensions` | object | no | See section 5. |

System: `name` (string, req), `description` (string, req), `version` (string, optional).

Goals: `q1` to `q7`, each an optional string in the schema. The validator requires `q1` and `q2`
(E104). See section 6.

Characteristic: `id` (string, req), `kind` (CharacteristicKind, req), `name` (optional),
`description` (optional). For kind `trustworthiness`, `id` must be a trustworthiness slug (E109).

InterrogationQuestion: `id` (req), `question` (req), `rationale` (optional).

### 3.2 Block

| Field | Type | Req | Description |
|---|---|---|---|
| `id` | string | yes | Unique within the plan. |
| `characteristics` | string[] | yes | Ids of characteristics the Block provides evidence for. |
| `definition` | string | yes | Precise definition of the concept measured. |
| `evidence_required` | string | yes | Evidence the Block needs. |
| `measures` | Measure[] | yes | Measures reported for the Block. |
| `extensions` | object | no | |

### 3.3 Measure

| Field | Type | Req | Description |
|---|---|---|---|
| `id` | string | yes | Unique within its Block. |
| `unit` | string | yes | For example `proportion` or `seconds`. |
| `direction` | MeasureDirection | yes | Which direction is preferable. |
| `target` | number | no | Reference value from goal Q6. Not a pass/fail threshold. |
| `extensions` | object | no | |

### 3.4 Event

| Field | Type | Req | Description |
|---|---|---|---|
| `id` | string | yes | Unique within the plan. |
| `type` | EventType | yes | Kind of Event. |
| `setting` | Setting | yes | How realistic the setting is. |
| `blocks` | string[] | yes | Ids of Blocks the Event produces evidence for. |
| `tools` | string[] | yes | Ids of Toolbox tools used. |
| `conditions` | object (string to string[]) | no | Experimental factors and their levels. |
| `description` | string | no | What the Event involves. |
| `extensions` | object | no | |

### 3.5 Tool

| Field | Type | Req | Description |
|---|---|---|---|
| `id` | string | yes | Unique within the Toolbox. |
| `kind` | string | yes | For example `eval_harness`, `questionnaire`, `annotation_schema`. |
| `ref` | ToolRef | yes | External tool or method: `name` (req), `version`, `url`. |
| `adapter` | Adapter | no | `type` (req) and `map` (source metric name to measure id). |
| `extensions` | object | no | |

### 3.6 EvidenceRecord (one line of `evidence/*.jsonl`)

| Field | Type | Req | Description |
|---|---|---|---|
| `event` | string | yes | Id of the Event. |
| `tool` | string | yes | Id of the Tool. |
| `block` | string | yes | Id of the Block. |
| `measure` | string | yes | Id of the measure within the Block. |
| `value` | boolean, integer, number or string | yes | Observed value. |
| `subject` | Subject | yes | `kind` and `id`, both strings. |
| `conditions` | object (string to string) | no | One level per Event condition factor. |
| `source` | Source | yes | `uri`, `sha256`, `adapter`, `adapter_version`, all strings. |
| `environment` | Environment | no | `model`, `version`, `config_hash`, all optional strings. |
| `collected_at` | date-time string | yes | When collected. |
| `extensions` | object | no | |

### 3.7 Review (`review.yaml`)

| Field | Type | Req | Description |
|---|---|---|---|
| `spec_version` | string | yes | Spec semver used. |
| `framework_ref` | string | yes | Framework edition followed. |
| `athlon` | string | yes | Id of the plan reviewed. |
| `interrogation` | InterrogationResponse[] | no | Each has `question` (id), `status` (InterrogationStatus), `response` (string), all required. |
| `limitations` | string[] | no | Known limitations. |
| `validity_boundary` | string | yes | Conditions under which results are expected to hold. |
| `extensions` | object | no | |

## 4. Vocabulary

Source: `src/tevv_athlon/model/vocab.py`.

**Trustworthiness characteristic ids** (`kind: trustworthiness`)

| Id | Name |
|---|---|
| `valid_reliable` | Valid and Reliable |
| `safe` | Safe |
| `secure_resilient` | Secure and Resilient |
| `accountable_transparent` | Accountable and Transparent |
| `explainable_interpretable` | Explainable and Interpretable |
| `privacy_enhanced` | Privacy-Enhanced |
| `fair` | Fair with Harmful Bias Managed |

**CharacteristicKind:** `trustworthiness`, `system_attribute`.

**EventType:** `benchmark`, `red_teaming`, `user_testing`, `field_testing`, `other`.

**Setting:** `controlled`, `semi_realistic`, `real_world`.

**LifecycleStage:** `plan_design`, `collect_process_data`, `build_use`, `deploy`, `operate_monitor`.

**MeasureDirection:** `higher_is_better`, `lower_is_better`, `neutral`.

**InterrogationStatus:** `addressed`, `partially_addressed`, `not_addressed`.

**Stages:** `articulate_organize`, `define_construct`, `apply_measure`, `synthesize_interrogate`.

## 5. The `extensions` rule

Unknown fields are rejected everywhere. The single exception is the optional `extensions` object,
present on every spec object, which may hold any JSON data beyond the NIST AI 200-2 ipd draft.
Consumers must ignore extension content they do not understand.

## 6. Goal questions

| Key | Question | Required |
|---|---|---|
| `q1` | What are the goals of the TEVV-Athlon, stated with no jargon? | yes |
| `q2` | Who cares, and what difference will the results make? | yes |
| `q3` | Approximately how much time and cost will it take? | no |
| `q4` | What resources are needed? | no |
| `q5` | What existing TEVV techniques does it build on? | no |
| `q6` | What leads to success? | no |
| `q7` | What are the challenges? | no |

## 7. Design rules

- No composite score and no pass/fail verdict. Measures are reported individually. A `target` is a
  reference shown beside the estimate, never a threshold.
- Generic conditions. Event `conditions` are free-form factors and levels; the spec does not
  hard-code any domain-specific factor.
- Pre-registered interrogation. Validity questions are written in `athlon.yaml` before testing and
  answered in `review.yaml` afterwards (W201 warns if none are registered).

## 8. Validator semantics

`tevv-athlon validate <athlon.yaml>` parses the plan with `yaml.safe_load`, checks the schema, then
runs cross-reference checks. If `spec_version` has a different major.minor, only E003 is reported.
If schema checks fail, only E002 issues are reported. Otherwise the semantic checks run. Each issue
has a JSON-pointer `path`, a `code`, a `severity` and a `message`; issues are sorted by path then
code. Codes starting with `E` are errors, `W` are warnings. Exit code is 0 if there are no errors,
1 if any error, 2 on usage error. In v0.1 only `athlon.yaml` is validated by the CLI.

| Code | Severity | Meaning |
|---|---|---|
| E001 | error | File is not parseable YAML or top level is not a mapping |
| E002 | error | Schema violation |
| E003 | error | Unsupported spec_version |
| E101 | error | Unknown block reference in event |
| E102 | error | Unknown tool reference in event |
| E103 | error | Unknown characteristic reference in block |
| E104 | error | Goal q1 or q2 missing or blank |
| E105 | error | Duplicate id |
| E106 | error | Adapter map target is not a measure of any block |
| E107 | error | Block not referenced by any event |
| E108 | error | Event has no tools |
| E109 | error | Unknown trustworthiness characteristic id |
| W201 | warning | Plan has no interrogation questions |
| W202 | warning | Tool not used by any event |

## 9. Conformance

The JSON Schemas are normative for structure. An independent JSON Schema (draft 2020-12)
validator, not using this package, must accept the example documents and reject documents with
unknown fields outside `extensions`. Semantic rules (section 8) go beyond JSON Schema and are
implemented only by the reference validator.

Examples and fixtures:

- `spec/examples/ambient-scribe/`: a worked example plan for an agentic system (the
  Action-Violation problem). It must validate cleanly.
- `spec/examples/ambient-scribe-illustrative/`: NOT REAL RESULTS / FOR EDUCATIONAL PURPOSES. The
  same plan with every event treated as run, plus made-up evidence and a review generated by
  `generate.py`, to show a fully populated TEVV-Athlon. Every record carries
  `extensions: {illustrative: true, label: ...}`. Its evidence and review must match their schemas
  and the plan (`tests/test_example_evidence.py`).
- `tests/fixtures/query-violation/`: the draft's chatbot worked example (Query-Violation) as a
  plan. It must validate cleanly.
- `tests/fixtures/broken/`: a plan that intentionally violates semantic rules, used to test the
  validator's issue codes.

## 10. Planned: report.json (non-normative)

This section is a plan, not a specification, and may change. `report.json` will be generated from
the plan, the evidence and the review. It is expected to report, per Block and measure, an estimate
with its uncertainty and the conditions it covers, alongside any `target` and the review's
interrogation answers, limitations and validity boundary. `report.html` will render the same data.
It will not contain a composite score or pass/fail verdict.
