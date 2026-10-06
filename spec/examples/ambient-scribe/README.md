# Testing an AI note-taker: the plan

This folder holds a real test plan, `athlon.yaml`, for an AI "note-taker" that listens to a
doctor's visit, writes the notes, and suggests updates to the patient's medical record for the
doctor to approve. **No test in this plan has been run yet**, so there are no results here.

To see what the same plan looks like with results filled in (made-up results, clearly
labeled), go to `../ambient-scribe-illustrative/` and its
[overview page](https://neems.github.io/athlon-schema/examples/ambient-scribe-illustrative/).

## How to read `athlon.yaml`

| Section | In plain words |
|---|---|
| `system`, `goals` | What is being tested, who cares about the results, and what could go wrong |
| `characteristics` | The kinds of trustworthiness we care about, such as safe, fair, and valid and reliable |
| `blocks` | The five things we measure, each with the exact numbers (`measures`) to collect |
| `events` | The five tests, such as a trick test where someone tries to make the AI do something unsafe |
| `toolbox` | What each test uses, such as a computer rule checker or a form doctors fill in |
| `interrogation` | Hard questions about the results, written down before any test runs |

The file is checked by `uv run tevv-athlon validate spec/examples/ambient-scribe/athlon.yaml`.
Everything in it is synthetic: there are no real patients, and it is not a medical device.
The program that would run the trick test is in `examples/ambient_scribe/`.
