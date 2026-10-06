# Testing an AI note-taker: a worked example (NOT REAL RESULTS / FOR EDUCATIONAL PURPOSES)

> **NOT REAL RESULTS / FOR EDUCATIONAL PURPOSES. This example is AI-generated and is not real
> data.** The visits, people, numbers and review in this folder were all made up with AI (the
> numbers by `generate.py`). No AI system was tested, and no real patients or doctors were
> involved. This project is not affiliated with or endorsed by NIST.

**Start here:** the [overview page](https://neems.github.io/athlon-schema/examples/ambient-scribe-illustrative/)
explains the whole example with pictures. You can also open `overview.html` in a browser.

## The idea in one minute

Some clinics are trying AI "note-takers". During a doctor's visit the AI listens, writes the
visit notes, and suggests updates to the patient's medical record, which the doctor approves
or rejects. Before trusting it, you would want to know:

1. Does the note match what was said?
2. Does it avoid unsafe changes to the medical record, even if someone tries to trick it?
3. Does it stop when the doctor says stop?
4. Does it speak up when something is unclear?
5. Does it work equally well for everyone, whatever their accent or however noisy the room?

NIST, a US government standards lab, has drafted a method for planning tests like this. You
write a plan, run several different tests, save every observation, and then ask hard
questions about what the results really show. This folder shows what all of that looks like
once it is finished, using made-up numbers.

## What is in this folder

| File | In plain words |
|---|---|
| `overview.html` | The page to read first: the story, the tests, charts of the results and a glossary |
| `athlon.yaml` | The test plan: what we care about, what we count, and which tests we run |
| `evidence/*.jsonl` | 532 saved observations, one per line, such as "in trick-test run 5 the AI suggested an unsafe change" |
| `review.yaml` | The written look-back that answers five hard questions about the results |
| `generate.py` | The program that made up all of the numbers above |

Every observation and every file here is labeled NOT REAL RESULTS and marked as AI-generated. A test in
`tests/test_example_evidence.py` fails if a label goes missing or if the files stop matching
what `generate.py` produces.

## Remaking the files

From the top folder of the repository:

```
uv run python spec/examples/ambient-scribe-illustrative/generate.py
```
