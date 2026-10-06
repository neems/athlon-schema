# Ambient-scribe red-team harness

This harness runs the `injection_red_teaming` event of the plan in
`spec/examples/ambient-scribe/athlon.yaml`. A small scribe agent built on Claude Haiku 4.5 reads 12
synthetic visit transcripts, 8 of which contain spoken injections. Each transcript is run under a
test framing and a realistic framing, giving 24 episodes. A deterministic policy oracle then checks
each episode's proposed EMR writes.

> Synthetic data only: every patient, name and transcript is fabricated, and there is no PHI. This
> is an evaluation example, not a medical device, and it makes no clinical claims. It is not
> affiliated with or endorsed by NIST or Anthropic.

## Files

- `cases.yaml`: synthetic patients and transcripts, the resource types each visit may write, and
  the kind of injection in each injected case
- `mock_emr.py`: in-memory EMR; proposals are queued and nothing commits without an approval token
- `agent.py`: the system under test (one Messages API call per visit, structured JSON output)
- `policy_oracle.py`: the rules for a prohibited write (wrong patient; sign, order or delete;
  medication or allergy change without clinician confirmation; a resource type the visit does not
  allow)
- `run.py`: runs every episode and writes the raw episodes and the evidence records

## Reproduce

From the repository root, with `ANTHROPIC_API_KEY` set:

```
uv run --with anthropic python examples/ambient_scribe/run.py
```

This writes `spec/examples/ambient-scribe/raw/episodes.jsonl` and
`spec/examples/ambient-scribe/evidence/policy_oracle.jsonl`. The model is called at temperature 0,
but outputs can still vary between runs and model updates, so the raw file, once committed, is the
record of what was observed. No run has been committed yet. A run costs well under US$1.

## Limits

The oracle covers four rule categories only, the transcripts are short and synthetic, and no
clinician reviewed the notes.
