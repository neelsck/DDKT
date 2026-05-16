"""Generate GBrain pages for the four Maria's Bakery contract FSM JSONs."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "gbrain_pages" / "marias_bakery"
CONTRACT_IDS = (
    "C_VAN_contract",
    "C_LEASE_contract",
    "C_SUPPLIER_contract",
    "C_WHOLESALE_contract",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _load_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def _transition_table(fsm: dict[str, Any]) -> str:
    rows = ["| Transition | Event | From | To | Guard | Effects |", "|---|---|---|---|---|---|"]
    for tr in fsm.get("transitions", []):
        effects = "; ".join(
            f"{effect.get('type', '')}: {effect.get('description', '')}"
            for effect in tr.get("effects", [])
        )
        rows.append(
            "| {id} | `{event}` | {from_states} | `{to}` | {guard} | {effects} |".format(
                id=tr.get("id", ""),
                event=tr.get("event_type", ""),
                from_states=", ".join(f"`{s}`" for s in tr.get("from_states", [])),
                to=tr.get("to_state", ""),
                guard=f"`{tr['guard']}`" if tr.get("guard") else "",
                effects=effects.replace("|", "/"),
            )
        )
    return "\n".join(rows)


def _state_table(fsm: dict[str, Any]) -> str:
    rows = ["| State | Terminal | Description |", "|---|---:|---|"]
    for state in fsm.get("states", []):
        rows.append(
            f"| `{state.get('id', '')}` | {bool(state.get('terminal'))} | {state.get('description', '').replace('|', '/')} |"
        )
    return "\n".join(rows)


def _contract_page(contract_id: str, fsm: dict[str, Any], contract_text: str) -> str:
    params = fsm.get("params", {})
    amounts = params.get("amounts", {})
    thresholds = params.get("thresholds", {})
    raw_json = json.dumps(fsm, indent=2)
    title = contract_id.replace("_", " ")
    return f"""---
type: contract-fsm
title: "Maria's Bakery - {title}"
tags: [marias-bakery, contract-fsm, executable-contract, fsm]
contract_id: {contract_id}
source_file: output/{contract_id}/fsm.json
---

# Maria's Bakery - {title}

This page ingests the finite state machine JSON for `{contract_id}`. The app uses this as contract-grounded retrieval context, then verifies proposed scenarios by replaying events through the FSM.

## Contract Facts

- Parties: {", ".join(fsm.get("parties", []))}
- Initial state: `{fsm.get("initial_state")}`
- State count: {len(fsm.get("states", []))}
- Transition count: {len(fsm.get("transitions", []))}
- Amounts: {json.dumps(amounts, sort_keys=True)}
- Thresholds: {json.dumps(thresholds, sort_keys=True)}

## States

{_state_table(fsm)}

## Transitions

{_transition_table(fsm)}

## Original Contract Text

```text
{contract_text.strip()}
```

## Raw FSM JSON

```json
{raw_json}
```

---

- {date.today().isoformat()}: Ingested from DDKT Maria's Bakery output JSON for scenario optimization and deterministic FSM verification.
"""


def _bundle_page() -> str:
    context = _load_text(ROOT / "marias_bakery_clean" / "context_question_expected_response.txt")
    return f"""---
type: contract-fsm-brief
title: "Maria's Bakery - Cross-Contract Decision Brief"
tags: [marias-bakery, contract-fsm, decision-brief, executable-contract]
---

# Maria's Bakery - Cross-Contract Decision Brief

This page connects the four ingested FSMs for business questions about route revenue, van readiness, landlord consent, insurance timing, supplier minimums, supplier rebates, late delivery credits, and termination risk.

The reasoner generates candidate scenarios, scores them against the user's desired outputs, then replays the event list through each FSM before presenting a recommendation.

## Source Context

```text
{context.strip()}
```

---

- {date.today().isoformat()}: Created as the cross-contract retrieval page for Maria's Bakery FSM optimization.
"""


def build_pages(out_dir: Path = OUT_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for contract_id in CONTRACT_IDS:
        fsm_path = ROOT / "output" / contract_id / "fsm.json"
        text_path = ROOT / "marias_bakery_clean" / "contracts" / f"{contract_id}.txt"
        page = _contract_page(contract_id, _load_json(fsm_path), _load_text(text_path))
        path = out_dir / f"{contract_id}.md"
        path.write_text(page)
        written.append(path)

    bundle_path = out_dir / "marias_bakery_decision_brief.md"
    bundle_path.write_text(_bundle_page())
    written.append(bundle_path)
    return written


def import_to_gbrain(out_dir: Path = OUT_DIR) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gbrain", "import", str(out_dir), "--no-embed", "--json"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-import", action="store_true", help="Only write markdown pages; do not call gbrain import.")
    args = parser.parse_args()

    pages = build_pages()
    print(f"Wrote {len(pages)} GBrain markdown pages to {OUT_DIR}")
    for path in pages:
        print(f"  {path.relative_to(ROOT)}")

    if args.no_import:
        return 0

    proc = import_to_gbrain()
    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip())
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
