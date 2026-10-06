# athlon-schema

A draft machine-readable file format for assessments conducted under the TEVV-Athlon Framework
(NIST AI 200-2 initial public draft, August 2026), with JSON Schemas and a reference validator.
The Python package and command-line tool are named `tevv-athlon`.

> **This is an independent project. It is not affiliated with or endorsed by NIST.** It records
> the outputs of the framework's four stages in a structured form. It does not modify or
> reinterpret the framework.

## Purpose

NIST AI 200-2 ipd describes what each stage of a TEVV-Athlon should produce but does not specify a
format for recording it. This project proposes one, so that plans and results from different
assessments can be compared, checked automatically and reviewed by others. It is meant as a
reference point for discussion, not as a proposed standard.

## Mapping to the framework

| Stage (NIST AI 200-2 ipd) | File | Contents |
|---|---|---|
| 1. Articulate & Organize (§2.1) | `athlon.yaml` | System description, answers to the seven goal questions, trustworthiness characteristics, lifecycle stage |
| 2. Define & Construct (§2.2) | `athlon.yaml` | Blocks, each with a definition, the evidence it requires, and measures (unit, direction, optional target) |
| 3. Apply & Measure (§2.3) | `athlon.yaml`, `evidence/*.jsonl` | Events (type, setting, condition factors) and the Toolbox in the plan; one evidence record per observation |
| 4. Synthesize & Interrogate (§2.4) | `athlon.yaml`, `review.yaml` | Interrogation questions registered in the plan before testing; responses, limitations and validity boundary in the review afterwards |

`athlon.yaml` is written before any testing takes place. The controlled vocabulary (the seven AI
RMF trustworthiness characteristics, Event types, settings and lifecycle stages) follows the draft
and is listed in [`spec/SPEC.md`](spec/SPEC.md) §4.

## Design choices

- **No composite score or pass/fail verdict.** Measures are reported individually. A `target` is
  optional, set per measure, and reported beside the estimate rather than used as a threshold.
- **Pre-registered interrogation.** Stage 4 questions are recorded in the plan before any results
  exist and answered in the review afterwards. The validator warns (W201) when none are registered.
- **Provenance on every evidence record.** Each record names its Event, Tool, Block and measure. It
  also carries the SHA-256 digest of its raw source, the adapter and adapter version that produced
  it, the run environment (model, version, configuration hash) and a collection timestamp.
- **Conditions carried through to Stage 4.** Events declare condition factors and their levels
  (for example speaker profile, audio noise, or test versus realistic framing), and each evidence
  record states the levels under which it was observed, so results can be compared across them.
- **Strict, versioned and extensible.** Unknown fields are rejected everywhere except inside an
  `extensions` object. Each schema has a versioned `$id`.

## Status

Draft, spec version 0.1.0. The format will change while NIST AI 200-2 remains a draft; version 1.0
is intended to align with the final publication. The package is not published to PyPI.

In this version the CLI validates `athlon.yaml` plans, checking both the schema and the
cross-references between goals, characteristics, Blocks, Events and Tools. Evidence and review files
are defined by their schemas and can be checked with any JSON Schema validator. Evidence adapters,
report generation and migration tooling are planned but not yet implemented.

## Schemas

JSON Schema draft 2020-12, generated from the Pydantic models in `src/tevv_athlon/model/`:

- https://neems.github.io/athlon-schema/schema/0.1/athlon.schema.json
- https://neems.github.io/athlon-schema/schema/0.1/evidence.schema.json
- https://neems.github.io/athlon-schema/schema/0.1/review.schema.json

The same files are in [`spec/schema/`](spec/schema/). Any JSON Schema validator that supports draft
2020-12 can use them. For example, with `check-jsonschema`:

```
uv run check-jsonschema --schemafile spec/schema/athlon.schema.json spec/examples/ambient-scribe/athlon.yaml
```

## Installation

Requires Python 3.11 or later.

```
git clone https://github.com/neems/athlon-schema.git
cd athlon-schema
uv sync
```

Alternatively, run `pip install .` from the clone.

## Usage

Run from the repository root.

```
$ uv run tevv-athlon validate spec/examples/ambient-scribe/athlon.yaml
spec/examples/ambient-scribe/athlon.yaml: 0 error(s), 0 warning(s)

$ uv run tevv-athlon validate tests/fixtures/broken/athlon.yaml
error E107 /blocks/1: Block 'orphan' is not referenced by any event
error E101 /events/0/blocks/1: Unknown block 'no_such_block'
error E102 /events/0/tools/1: Unknown tool 'no_such_tool'
error E104 /goals/q2: Goal q2 is missing or blank
tests/fixtures/broken/athlon.yaml: 4 error(s), 0 warning(s)
```

`validate` exits 0 when there are no errors, 1 when there are errors and 2 on a usage error. Add
`--format json` for machine-readable output. `tevv-athlon codes` lists every issue code with a fix
hint, and `tevv-athlon schema export --check` confirms that `spec/schema/` matches the models.

## Examples

| Path | Description |
|---|---|
| `tests/fixtures/query-violation/` | The draft's worked example (§3, the Query-Violation problem) encoded as a plan |
| `spec/examples/ambient-scribe/` | A plan for an agentic system: an ambient clinical scribe that drafts a visit note and proposes medical-record writes for clinician approval (an Action-Violation problem). Plan only; no Event has been run. |
| `examples/ambient_scribe/` | A red-teaming harness for one Event of that plan, using synthetic transcripts and a deterministic policy oracle |
| `spec/examples/ambient-scribe-illustrative/` | The same plan populated with synthetic evidence and a review, to show a complete set of files. **The results are fabricated for illustration and are not measurements.** A rendered walkthrough is [published here](https://neems.github.io/athlon-schema/examples/ambient-scribe-illustrative/). |

All examples use synthetic data. None contains protected health information, and none describes a
medical device.

## Repository layout

- `spec/SPEC.md`: the specification (field reference, vocabulary, validator rules, conformance)
- `spec/schema/`: generated JSON Schemas
- `spec/examples/`: example plans, evidence and reviews
- `src/tevv_athlon/`: data models, validator, schema export and CLI
- `tests/`: test suite and fixtures

## Development

```
uv run pytest
uv run ruff check
uv run pyright
uv run tevv-athlon schema export   # regenerate spec/schema/ after changing the models
```

## Feedback

Issues and pull requests are welcome at https://github.com/neems/athlon-schema/issues.
Corrections to how the format represents the draft are particularly useful.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
