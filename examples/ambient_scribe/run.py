"""Run the injection red-teaming event and write raw episodes plus evidence records.

Usage, from the repository root:

    uv run --with anthropic python examples/ambient_scribe/run.py

Needs Anthropic API credentials (ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN or an
`ant auth login` profile). Writes, under spec/examples/ambient-scribe/:
  raw/episodes.jsonl            one object per episode, including the model's full output
  evidence/policy_oracle.jsonl  one EvidenceRecord per episode
"""

import hashlib
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import anthropic
import yaml
from agent import FRAMINGS, INSTRUCTIONS, MODEL, OUTPUT_SCHEMA, run_episode
from mock_emr import MockEMR
from policy_oracle import judge

from tevv_athlon.model.evidence import Environment, EvidenceRecord, Source, Subject

HARNESS_VERSION = "0.1.0"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXAMPLE = ROOT / "spec" / "examples" / "ambient-scribe"
RAW = EXAMPLE / "raw" / "episodes.jsonl"
EVIDENCE = EXAMPLE / "evidence" / "policy_oracle.jsonl"

# Haiku 4.5 list prices, US$ per million tokens, used only for the cost estimate printed at the end.
PRICE_IN, PRICE_OUT = 1.00, 5.00


def have_credentials() -> bool:
    return bool(
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        or shutil.which("ant")
        or (Path.home() / ".config" / "anthropic").exists()
    )


def config_hash(cases_bytes: bytes) -> str:
    h = hashlib.sha256()
    h.update(INSTRUCTIONS.encode())
    h.update(json.dumps(FRAMINGS, sort_keys=True).encode())
    h.update(json.dumps(OUTPUT_SCHEMA, sort_keys=True).encode())
    h.update(cases_bytes)
    return h.hexdigest()


def main() -> int:
    if not have_credentials():
        print("No Anthropic credentials found. Export ANTHROPIC_API_KEY first.", file=sys.stderr)
        return 2
    cases_bytes = (HERE / "cases.yaml").read_bytes()
    data = yaml.safe_load(cases_bytes)
    emr = MockEMR(patients=data["patients"])
    client = anthropic.Anthropic()

    episodes = []
    for case in data["cases"]:
        for framing in ("test", "realistic"):
            episode_id = f"{case['id']}/{framing}"
            result = run_episode(client, framing, emr.context(case["patient"]), case["transcript"])
            writes = (result.get("output") or {}).get("proposed_writes", [])
            emr.propose(writes)
            violations = judge(writes, case["patient"], set(case["allowed_resources"]))
            episodes.append(
                {
                    "episode_id": episode_id,
                    "case_id": case["id"],
                    "framing": framing,
                    "visit_type": case["visit_type"],
                    "patient_id": case["patient"],
                    "injection": case["injection"],
                    **result,
                    "violations": violations,
                    "prohibited": bool(violations),
                    "committed_writes": emr.commit(approval_token=None),
                    "collected_at": datetime.now(UTC).isoformat(),
                }
            )
            print(f"{episode_id}: {result['outcome']}, prohibited={bool(violations)}")

    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in episodes))
    raw_sha = hashlib.sha256(RAW.read_bytes()).hexdigest()

    env = Environment(
        model=episodes[0]["model"] if episodes else MODEL,
        version=f"harness {HARNESS_VERSION}; anthropic-sdk {anthropic.__version__}",
        config_hash=config_hash(cases_bytes),
    )
    source = Source(
        uri="raw/episodes.jsonl",
        sha256=raw_sha,
        adapter="ambient-scribe-harness",
        adapter_version=HARNESS_VERSION,
    )
    records = [
        EvidenceRecord(
            event="injection_red_teaming",
            tool="policy_oracle",
            block="unauthorized_write_frequency",
            measure="prohibited_write_episode_share",
            value=e["prohibited"],
            subject=Subject(kind="episode", id=e["episode_id"]),
            conditions={"framing": e["framing"], "visit_type": e["visit_type"]},
            source=source,
            environment=env,
            collected_at=datetime.fromisoformat(e["collected_at"]),
        )
        for e in episodes
    ]
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text("".join(r.model_dump_json(exclude_none=True) + "\n" for r in records))

    tokens_in = sum(e["usage"]["input_tokens"] for e in episodes)
    tokens_out = sum(e["usage"]["output_tokens"] for e in episodes)
    cost = (tokens_in * PRICE_IN + tokens_out * PRICE_OUT) / 1_000_000
    prohibited = sum(e["prohibited"] for e in episodes)
    print(f"{len(episodes)} episodes, {prohibited} with a prohibited write")
    print(f"tokens in={tokens_in} out={tokens_out}, estimated cost ${cost:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
