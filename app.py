#!/usr/bin/env python3
"""HTTP server for Babel — upload contracts, visualize FSMs, ask questions."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from metrics import (
    compute_context_precision,
    compute_context_recall,
    compute_faithfulness,
)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent
UI_PATH = ROOT / "ui.html"
OUTPUT_DIR = ROOT / ".runtime_output"
GBRAIN_ROOT = ROOT / "gbrain_pages"
GBRAIN_FSM_DIR = GBRAIN_ROOT / "contract_fsm"
GBRAIN_RUN_DIR = GBRAIN_ROOT / "agent_runs"
GBRAIN_TIMEOUT_SECONDS = 30

AGENT_PROFILES = [
    {
        "id": "fraught",
        "name": "Fraught / Risk Agent",
        "focus": "failure modes, defaults, fragility, termination paths, blocked transitions",
        "query_terms": "risk default cure termination force majeure breach blocked infeasible",
        "system": (
            "You are the Fraught / Risk Agent. You specialize in what can go wrong: "
            "defaults, operational fragility, blocked states, termination, cure periods, "
            "force majeure, and hidden failure modes."
        ),
    },
    {
        "id": "shipping",
        "name": "Shipping / Operations Agent",
        "focus": "delivery performance, logistics, timing, routes, supplier and vehicle operations",
        "query_terms": "shipping delivery route supplier vehicle deadline milestone late on-time",
        "system": (
            "You are the Shipping / Operations Agent. You specialize in delivery, logistics, "
            "routes, timing, supplier performance, vehicles, and practical operational execution."
        ),
    },
    {
        "id": "legal",
        "name": "Legal / Remedies Agent",
        "focus": "contract rights, remedies, notice, cure, consent, enforcement mechanics",
        "query_terms": "legal remedy notice cure consent obligation prohibition warranty covenant",
        "system": (
            "You are the Legal / Remedies Agent. You specialize in contract rights, remedies, "
            "notice, cure, consent, warranties, covenants, and what the FSM actually authorizes. "
            "You are not giving legal advice; you are analyzing the executable contract model."
        ),
    },
    {
        "id": "ip",
        "name": "IP / Data Agent",
        "focus": "ownership, intellectual property, confidential information, brand, data, assignment",
        "query_terms": "intellectual property IP data confidentiality brand ownership assignment license",
        "system": (
            "You are the IP / Data Agent. You specialize in IP, ownership, brand, confidential "
            "information, licensing, assignment, and data rights. If the FSMs do not encode an IP issue, "
            "say that clearly and identify the nearest related clauses."
        ),
    },
    {
        "id": "finance",
        "name": "Finance / Commercial Agent",
        "focus": "payments, incentives, penalties, caps, credits, rebates, cash timing",
        "query_terms": "payment penalty incentive rebate credit cap holdback cash amount formula",
        "system": (
            "You are the Finance / Commercial Agent. You specialize in monetary outcomes, "
            "payment timing, penalties, rebates, caps, credits, incentives, and cash exposure."
        ),
    },
]


def _json_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Not serializable: {type(obj)}")


def _load_existing_fsms() -> dict[str, dict]:
    contracts: dict[str, dict] = {}
    if OUTPUT_DIR.is_dir():
        for fsm_path in OUTPUT_DIR.glob("*/fsm.json"):
            cid = fsm_path.parent.name
            try:
                contracts[cid] = json.loads(fsm_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
    return contracts


def _clear_runtime_state() -> None:
    """Start each app run without stale uploaded contracts or app-written GBrain pages."""
    for page_dir in (GBRAIN_FSM_DIR, GBRAIN_RUN_DIR):
        if page_dir.is_dir():
            for page in page_dir.glob("*.md"):
                for slug in {page.stem, _safe_slug(page.stem), f"{page_dir.name}/{page.stem}"}:
                    _gbrain_cli(["delete", slug], timeout=10)

    for path in (OUTPUT_DIR, GBRAIN_FSM_DIR, GBRAIN_RUN_DIR):
        if path.exists():
            shutil.rmtree(path)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


_contracts: dict[str, dict] = {}
_lock = threading.Lock()
_gbrain_lock = threading.Lock()
_gbrain_status: dict = {"available": False, "output": "GBrain has not been synced yet."}


def _fsm_to_dict(fsm) -> dict:
    """Serialize an FSMDefinition dataclass to a plain dict for JSON output."""
    def _rule(r):
        return {
            "id": r.id, "type": r.type.value, "party": r.party,
            "counterparty": r.counterparty, "action": r.action,
            "activation": r.activation.value, "description": r.description,
            "mappable": r.mappable, "unmappable_reason": r.unmappable_reason,
            "triggers": [{k: v for k, v in {
                "id": t.id, "type": t.type.value, "condition": t.condition,
                "reference_date": t.reference_date, "duration": t.duration,
                "duration_days": t.duration_days, "threshold_field": t.threshold_field,
                "threshold_value": t.threshold_value, "threshold_operator": t.threshold_operator,
            }.items() if v is not None} for t in r.triggers],
            "effects": [{k: v for k, v in {
                "id": e.id, "type": e.type.value, "description": e.description,
                "target_rule_id": e.target_rule_id, "payment_formula": e.payment_formula,
                "payment_from": e.payment_from, "payment_to": e.payment_to,
                "cap": str(e.cap) if e.cap is not None else None, "new_state": e.new_state,
            }.items() if v is not None} for e in r.effects],
            "constraints": [{k: v for k, v in {
                "id": c.id, "type": c.type.value,
                "value": str(c.value) if c.value is not None else None,
                "duration": c.duration, "duration_days": c.duration_days,
                "scope": c.scope or None, "description": c.description or None,
            }.items() if v is not None} for c in r.constraints],
            "exceptions": r.exceptions,
        }

    return {
        "contract_id": fsm.contract_id, "parties": fsm.parties,
        "initial_state": fsm.initial_state,
        "params": {
            "parties": fsm.params.parties, "base_dates": fsm.params.base_dates,
            "amounts": fsm.params.amounts, "rates": fsm.params.rates,
            "durations": fsm.params.durations, "thresholds": fsm.params.thresholds,
        },
        "states": [{"id": s.id, "description": s.description, "terminal": s.terminal,
                     "active_rule_ids": s.active_rule_ids} for s in fsm.states],
        "transitions": [{"id": t.id, "from_states": t.from_states, "to_state": t.to_state,
                          "event_type": t.event_type, "guard": t.guard,
                          "effects": t.effects, "description": t.description}
                         for t in fsm.transitions],
        "rules": [_rule(r) for r in fsm.rules],
        "unmappable_rules": [_rule(r) for r in fsm.unmappable_rules],
    }


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "contract"


def _command_output(result: subprocess.CompletedProcess) -> str:
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return output.strip()


def _run_command(args: list[str], timeout: int = GBRAIN_TIMEOUT_SECONDS) -> dict:
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        output = _command_output(result)
        return {
            "available": result.returncode == 0,
            "returncode": result.returncode,
            "output": output or "(no output)",
        }
    except FileNotFoundError:
        return {"available": False, "returncode": 127, "output": f"{args[0]} is not installed."}
    except subprocess.TimeoutExpired:
        return {"available": False, "returncode": 124, "output": f"{args[0]} timed out."}
    except Exception as exc:
        return {"available": False, "returncode": 1, "output": str(exc)}


def _gbrain_cli(args: list[str], timeout: int = GBRAIN_TIMEOUT_SECONDS) -> dict:
    if not shutil.which("gbrain"):
        return {
            "available": False,
            "returncode": 127,
            "output": "gbrain CLI is not installed or not on PATH.",
        }
    return _run_command(["gbrain", *args], timeout=timeout)


def _truncate_text(text: str, max_chars: int = 6000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[truncated]"


def _contract_to_gbrain_markdown(cid: str, fsm: dict) -> str:
    params = fsm.get("params", {}) or {}
    amounts = params.get("amounts") or {}
    states = fsm.get("states", [])
    transitions = fsm.get("transitions", [])
    rules = fsm.get("rules", [])
    unmappable = fsm.get("unmappable_rules", [])

    state_lines = "\n".join(
        f"- `{s.get('id')}`: {s.get('description', '')}"
        + (" (terminal)" if s.get("terminal") else "")
        for s in states
    ) or "- None"
    transition_lines = "\n".join(
        f"- `{t.get('id')}`: `{', '.join(t.get('from_states') or [])}` "
        f"--{t.get('event_type')}--> `{t.get('to_state')}`"
        + (f" when `{t.get('guard')}`" if t.get("guard") else "")
        + (f". {t.get('description')}" if t.get("description") else "")
        for t in transitions
    ) or "- None"
    rule_lines = "\n".join(
        f"- `{r.get('id')}` [{r.get('type')}]: {r.get('party')} -> {r.get('counterparty')}; "
        f"{r.get('action')}. {r.get('description') or ''}"
        for r in rules
    ) or "- None"
    unmappable_lines = "\n".join(
        f"- `{r.get('id')}` [{r.get('type')}]: {r.get('description') or r.get('action')}; "
        f"reason: {r.get('unmappable_reason') or 'not mapped'}"
        for r in unmappable
    ) or "- None"
    amount_lines = "\n".join(f"- `{key}`: {value}" for key, value in amounts.items()) or "- None"

    return (
        "---\n"
        "type: contract_fsm\n"
        f"title: {cid}\n"
        "tags: [contract-fsm, babel, shared-gbrain-memory]\n"
        "---\n\n"
        f"# {cid}\n\n"
        "Compiled truth: this page is the shared GBrain memory representation of one "
        "finite state machine contract. Specialist agents should use it as context, "
        "then validate suggested scenarios against the executable FSM states, transitions, and rules.\n\n"
        f"- Contract ID: `{fsm.get('contract_id', cid)}`\n"
        f"- Parties: {', '.join(fsm.get('parties', [])) or 'Unknown'}\n"
        f"- Initial state: `{fsm.get('initial_state')}`\n"
        f"- State count: {len(states)}\n"
        f"- Transition count: {len(transitions)}\n"
        f"- Rule count: {len(rules)}\n\n"
        "## Commercial Amounts\n"
        f"{amount_lines}\n\n"
        "## States\n"
        f"{state_lines}\n\n"
        "## Transitions\n"
        f"{transition_lines}\n\n"
        "## Rules\n"
        f"{rule_lines}\n\n"
        "## Unmappable Rules\n"
        f"{unmappable_lines}\n\n"
        "---\n\n"
        f"- {date.today().isoformat()}: Synced from uploaded contract FSM JSON into GBrain memory.\n\n"
        "## Raw FSM JSON\n"
        "```json\n"
        f"{json.dumps(fsm, indent=2, default=_json_default)}\n"
        "```\n"
    )


def _write_gbrain_contract_pages(contracts: dict[str, dict]) -> list[Path]:
    GBRAIN_FSM_DIR.mkdir(parents=True, exist_ok=True)
    for old_page in GBRAIN_FSM_DIR.glob("*.md"):
        old_page.unlink()

    written = []
    for cid, fsm in sorted(contracts.items()):
        path = GBRAIN_FSM_DIR / f"{_safe_slug(cid)}.md"
        path.write_text(_contract_to_gbrain_markdown(cid, fsm))
        written.append(path)
    return written


def _sync_contracts_to_gbrain(contracts: dict[str, dict]) -> dict:
    global _gbrain_status
    with _gbrain_lock:
        if not contracts:
            _gbrain_status = {
                "available": False,
                "output": "No FSMs loaded, so there is nothing to sync into GBrain.",
            }
            return dict(_gbrain_status)

        pages = _write_gbrain_contract_pages(contracts)
        result = _gbrain_cli(["import", str(GBRAIN_FSM_DIR), "--no-embed", "--json"], timeout=60)
        output = (
            f"Synced {len(pages)} FSM page(s) into GBrain from {GBRAIN_FSM_DIR.relative_to(ROOT)}.\n"
            f"{result.get('output', '')}"
        )
        _gbrain_status = {
            "available": bool(result.get("available")),
            "output": output.strip(),
            "page_count": len(pages),
            "path": str(GBRAIN_FSM_DIR.relative_to(ROOT)),
        }
        return dict(_gbrain_status)


def _gbrain_memory_search(question: str, focus: str = "") -> tuple[dict, str]:
    query = question.strip() or focus.strip() or "uploaded contract FSM"
    query = query[:700]
    result = _gbrain_cli(["search", query], timeout=GBRAIN_TIMEOUT_SECONDS)
    output = result.get("output", "")
    if result.get("available") and output.strip() and output.strip() != "No results.":
        raw_text = output
        truncated_text = _truncate_text(raw_text)
        return {
            "available": True,
            "query": query,
            "output": truncated_text,
            "returncode": result.get("returncode"),
        }, raw_text

    fallback_pages = []
    for page in sorted(GBRAIN_FSM_DIR.glob("*.md")):
        get_result = _gbrain_cli(["get", page.stem], timeout=GBRAIN_TIMEOUT_SECONDS)
        if get_result.get("available") and get_result.get("output"):
            fallback_pages.append(
                f"## {page.stem}\n{get_result['output']}"
            )

    if fallback_pages:
        raw_text = (
            f"GBrain search for `{query}` returned no direct hits, so this agent loaded "
            "the canonical imported FSM memory pages by slug.\n\n"
            + "\n\n".join(fallback_pages)
        )
        truncated_text = _truncate_text(raw_text)
        return {
            "available": True,
            "query": query,
            "output": truncated_text,
            "returncode": result.get("returncode"),
        }, raw_text

    raw_text = output if result.get("available") else ""
    return {
        "available": bool(result.get("available")),
        "query": query,
        "output": output,
        "returncode": result.get("returncode"),
    }, raw_text


def _build_fsm_context(contracts: dict[str, dict]) -> str:
    parts = []
    for cid, fsm in contracts.items():
        states = "\n".join(
            f"  - {s['id']}: {s['description']}"
            + (" (terminal)" if s.get("terminal") else "")
            for s in fsm.get("states", [])
        )
        trans = "\n".join(
            f"  - {t['id']}: {t['from_states']} on '{t['event_type']}' -> {t['to_state']}"
            + (f" [guard: {t['guard']}]" if t.get("guard") else "")
            for t in fsm.get("transitions", [])
        )
        rules = "\n".join(
            f"  - {r['id']} [{r['type']}]: {r['action']}"
            for r in fsm.get("rules", []) if r.get("mappable", True)
        )
        params = fsm.get("params", {})
        amounts = ", ".join(f"{k}: ${v}" for k, v in (params.get("amounts") or {}).items())
        parts.append(
            f"Contract: {cid}\n"
            f"Parties: {', '.join(fsm.get('parties', []))}\n"
            f"Initial State: {fsm.get('initial_state')}\n"
            f"Amounts: {amounts}\n\n"
            f"States:\n{states}\n\n"
            f"Transitions:\n{trans}\n\n"
            f"Rules:\n{rules}"
        )
    return "\n\n---\n\n".join(parts)


def _message_text(message) -> str:
    return "\n".join(
        getattr(block, "text", "")
        for block in getattr(message, "content", [])
        if getattr(block, "type", "text") == "text"
    ).strip()


def _run_specialist_agent(profile: dict, question: str, contracts: dict[str, dict]) -> dict:
    memory, raw_retrieved = _gbrain_memory_search(
        question,
        f"{profile['focus']} {profile['query_terms']}",
    )

    try:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=700,
            system=(
                f"{profile['system']} You are one of several specialist agents sharing the same "
                "GBrain memory. Use the GBrain search results as memory, then check any claim "
                "against the loaded finite state machines. Use state, transition, and rule IDs only "
                "for your internal validation; do not expose raw IDs, variable names, or all-caps "
                "state names in the user-facing bullets. "
                "Do not invent missing clauses. No AI fluff, no setup, no methodology. "
                "Return only short, direct bullet sentences for a small-business owner."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    f"Your focus:\n{profile['focus']}\n\n"
                    f"Shared GBrain memory search query:\n{memory.get('query')}\n\n"
                    f"Shared GBrain memory results:\n{memory.get('output') or 'No GBrain hits.'}\n\n"
                    f"Loaded FSM context:\n{_build_fsm_context(contracts)}\n\n"
                    "Return exactly 4 concise bullet sentences. No headings, no intro, "
                    "no tables, no labels like 'specialist read'. Each bullet must directly answer "
                    "the question from your expert focus in plain English. Do not include raw IDs like "
                    "C_..., TR..., R..., variable names, or all-caps state names."
                ),
            }],
        )
        output = _message_text(msg)
        available = True
    except ImportError:
        output = "Anthropic SDK not available. Install with: pip install anthropic"
        available = False
    except Exception as exc:
        output = f"Error querying specialist agent: {exc}"
        available = False

    return {
        "id": profile["id"],
        "name": profile["name"],
        "focus": profile["focus"],
        "available": available,
        "memory": memory,
        "output": output,
        "raw_retrieved": raw_retrieved,
    }


def _run_specialist_agents(question: str, contracts: dict[str, dict]) -> list[dict]:
    agents: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(AGENT_PROFILES)) as executor:
        futures = {
            executor.submit(_run_specialist_agent, profile, question, contracts): profile
            for profile in AGENT_PROFILES
        }
        for future in as_completed(futures):
            try:
                agents.append(future.result())
            except Exception as exc:
                profile = futures[future]
                agents.append({
                    "id": profile["id"],
                    "name": profile["name"],
                    "focus": profile["focus"],
                    "available": False,
                    "memory": {"available": False, "output": ""},
                    "output": f"Agent failed: {exc}",
                    "raw_retrieved": "",
                })

    order = {profile["id"]: index for index, profile in enumerate(AGENT_PROFILES)}
    return sorted(agents, key=lambda agent: order.get(agent["id"], 999))


def _synthesize_agents(question: str, contracts: dict[str, dict], agents: list[dict]) -> dict:
    agent_context = "\n\n".join(
        f"## {agent['name']}\n"
        f"Focus: {agent['focus']}\n"
        f"GBrain query: {agent.get('memory', {}).get('query', '')}\n"
        f"GBrain results:\n{agent.get('memory', {}).get('output', '')}\n\n"
        f"Agent output:\n{agent.get('output', '')}"
        for agent in agents
    )

    try:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system=(
                "You are the synthesizer for a multi-agent contract FSM system. "
                "The specialist agents all queried the same GBrain memory, but the final answer "
                "must be grounded in the executable FSMs. Recommend only scenarios that can actually "
                "play out through available states, transitions, and rules. Use IDs only internally; "
                "do not expose raw IDs, variable names, or all-caps state names. If agents disagree, "
                "resolve the disagreement by prioritizing the FSM validation path. Write for a busy "
                "mom-and-pop business owner. No AI fluff, no intro, no legal essay, no methodology. "
                "Only concise plain-English bullets that directly answer the user's question."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"User question:\n{question}\n\n"
                    f"Loaded FSM context:\n{_build_fsm_context(contracts)}\n\n"
                    f"Specialist agent outputs:\n{agent_context}\n\n"
                    "Return exactly 3-4 short bullet sentences. No headings, no intro, no tables, "
                    "no 'final answer' label, no memory note. Each bullet must directly answer the "
                    "user's question and include the practical action or warning in plain English. "
                    "Do not include raw FSM IDs, variable names, or all-caps state names."
                ),
            }],
        )
        synthesized_answer_text = _message_text(msg)
    except ImportError:
        synthesized_answer_text = "Anthropic SDK not available. Install with: pip install anthropic"
    except Exception as exc:
        synthesized_answer_text = f"Error synthesizing agents: {exc}"

    return {
        "answer": synthesized_answer_text,
        "metrics_input": {
            "agent_results": agents,
            "retrieved_per_agent": [
                {
                    "agent_id": agent["id"],
                    "retrieved": agent.get("raw_retrieved", ""),
                    "agent_output": agent.get("output", ""),
                }
                for agent in agents
            ],
        },
    }


def _persist_agent_run(question: str, agents: list[dict], answer: str, metrics: dict = None) -> dict:
    GBRAIN_RUN_DIR.mkdir(parents=True, exist_ok=True)
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{_safe_slug(question)[:48]}"
    path = GBRAIN_RUN_DIR / f"{run_id}.md"
    agent_sections = "\n\n".join(
        f"## {agent['name']}\n\n"
        f"Focus: {agent['focus']}\n\n"
        f"GBrain query: `{agent.get('memory', {}).get('query', '')}`\n\n"
        "### GBrain Hits\n"
        f"{agent.get('memory', {}).get('output', '') or 'No hits.'}\n\n"
        "### Agent Output\n"
        f"{agent.get('output', '')}"
        for agent in agents
    )

    content = (
        "---\n"
        "type: agent_run\n"
        f"title: Multi-agent FSM synthesis {run_id}\n"
        "tags: [contract-fsm, babel, agent-run, shared-gbrain-memory]\n"
        "---\n\n"
        f"# Multi-agent FSM synthesis: {question}\n\n"
        "Compiled truth: this page records one multi-agent run over the uploaded contract FSM memory. "
        "Future specialist agents should search this run when answering related questions.\n\n"
        "## Question\n"
        f"{question}\n\n"
        "## Final Synthesis\n"
        f"{answer}\n\n"
        "## Specialist Agent Outputs\n"
        f"{agent_sections}\n\n"
        "---\n\n"
        f"- {date.today().isoformat()}: Written back after specialist agents shared GBrain memory and synthesized an FSM-validated answer.\n"
    )

    # METRICS NOT PERSISTED TO GBRAIN: _persist_agent_run() is called before
    # metrics are computed in the streaming path. The metrics section is only
    # written when a future caller passes a populated metrics dict.
    if metrics:
        content += "\n\n## Evaluation Metrics\n\n"
        content += (
            f"**Faithfulness:** "
            f"{metrics.get('faithfulness', {}).get('score', 'n/a')}\n"
        )
        content += (
            f"**Context Recall:** "
            f"{metrics.get('context_recall', {}).get('score', 'n/a')}\n"
        )
        content += (
            f"**Context Precision:** "
            f"{metrics.get('context_precision', {}).get('score', 'n/a')}\n"
        )

    path.write_text(content)

    result = _gbrain_cli(["import", str(GBRAIN_RUN_DIR), "--no-embed", "--json"], timeout=60)
    return {
        "available": bool(result.get("available")),
        "path": str(path.relative_to(ROOT)),
        "output": result.get("output", ""),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "ContractFSM/0.1"

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, indent=2, default=_json_default).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse_headers(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

    def _send_sse_event(self, event: str, payload: dict):
        body = (
            f"event: {event}\n"
            f"data: {json.dumps(payload, default=_json_default)}\n\n"
        ).encode()
        self.wfile.write(body)
        self.wfile.flush()

    def _send_html(self, text):
        body = text.encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    # ── GET ────────────────────────────────────────────────────────────────────

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            self._send_html(UI_PATH.read_text())
            return
        if path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        if path == "/api/ask/stream":
            self._handle_ask_stream(parsed.query)
            return
        if path == "/api/contracts":
            with _lock:
                summaries = []
                for cid, fsm in _contracts.items():
                    summaries.append({
                        "contract_id": cid,
                        "parties": fsm.get("parties", []),
                        "initial_state": fsm.get("initial_state"),
                        "state_count": len(fsm.get("states", [])),
                        "transition_count": len(fsm.get("transitions", [])),
                        "rule_count": len(fsm.get("rules", [])),
                        "event_types": sorted(
                            {t.get("event_type", "") for t in fsm.get("transitions", [])}
                        ),
                    })
            self._send_json({"contracts": summaries})
            return
        if path.startswith("/api/fsm/"):
            cid = path[len("/api/fsm/"):]
            with _lock:
                fsm = _contracts.get(cid)
            if fsm:
                self._send_json(fsm)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, f"Contract {cid} not found")
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    # ── POST ───────────────────────────────────────────────────────────────────

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/upload":
            self._handle_upload()
        elif path == "/api/ask":
            self._handle_ask()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _handle_upload(self):
        try:
            payload = self._read_body()
            files = payload.get("files", [])
            if not files:
                raise ValueError("No files provided")

            results = []
            for f in files:
                name = f.get("name", "contract.txt")
                content = f.get("content", "")
                if not content.strip():
                    results.append({"name": name, "error": "Empty file"})
                    continue

                ext = Path(name).suffix.lower()
                contract_id = Path(name).stem

                if ext == ".json":
                    try:
                        fsm_data = json.loads(content)
                        if "states" not in fsm_data or "transitions" not in fsm_data:
                            raise ValueError("Not a valid FSM JSON (missing states or transitions)")
                        cid = fsm_data.get("contract_id", contract_id)
                        with _lock:
                            _contracts[cid] = fsm_data
                        results.append({
                            "name": name, "contract_id": cid, "ok": True, "mode": "direct",
                            "state_count": len(fsm_data.get("states", [])),
                            "transition_count": len(fsm_data.get("transitions", [])),
                        })
                    except json.JSONDecodeError as exc:
                        results.append({"name": name, "error": f"Invalid JSON: {exc}"})
                else:
                    try:
                        from contracts.pipeline import run_pipeline
                        result = run_pipeline(content, contract_id=contract_id)
                        fsm_dict = _fsm_to_dict(result.fsm)

                        out_dir = OUTPUT_DIR / contract_id
                        out_dir.mkdir(parents=True, exist_ok=True)
                        (out_dir / "fsm.json").write_text(
                            json.dumps(fsm_dict, indent=2, default=_json_default)
                        )
                        (out_dir / "english.txt").write_text(result.english)

                        with _lock:
                            _contracts[contract_id] = fsm_dict

                        results.append({
                            "name": name, "contract_id": contract_id, "ok": True,
                            "mode": "pipeline",
                            "state_count": len(fsm_dict.get("states", [])),
                            "transition_count": len(fsm_dict.get("transitions", [])),
                            "validation_issues": result.validation_issues,
                        })
                    except Exception as exc:
                        results.append({
                            "name": name, "contract_id": contract_id,
                            "ok": False, "error": str(exc),
                        })

            with _lock:
                contracts = dict(_contracts)
            gbrain = _sync_contracts_to_gbrain(contracts)

            self._send_json({"results": results, "gbrain": gbrain})
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _handle_ask(self):
        try:
            payload = self._read_body()
            question = str(payload.get("question", "")).strip()
            if not question:
                raise ValueError("question is required")

            with _lock:
                contracts = dict(_contracts)

            gbrain = _sync_contracts_to_gbrain(contracts)
            agents = _run_specialist_agents(question, contracts)
            synthesis_result = _synthesize_agents(question, contracts, agents)
            answer = synthesis_result["answer"]
            memory_write = _persist_agent_run(question, agents, answer, metrics=None)

            self._send_json({
                "question": question,
                "answer": answer,
                "gbrain": gbrain,
                "agents": agents,
                "memory_write": memory_write,
            })
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _handle_ask_stream(self, query: str):
        self._send_sse_headers()

        def emit(event: str, payload: dict):
            self._send_sse_event(event, payload)

        try:
            params = parse_qs(query)
            question = (params.get("question", [""])[0] or "").strip()
            if not question:
                emit("server_error", {"error": "question is required"})
                return

            with _lock:
                contracts = dict(_contracts)

            emit("status", {
                "stage": "gbrain_sync",
                "message": "Loading the contract memory.",
            })
            gbrain = _sync_contracts_to_gbrain(contracts)
            emit("gbrain", gbrain)

            emit("status", {
                "stage": "fanout",
                "message": f"Asking {len(AGENT_PROFILES)} specialist agents.",
            })

            agents: list[dict] = []
            with ThreadPoolExecutor(max_workers=len(AGENT_PROFILES)) as executor:
                futures = {}
                for profile in AGENT_PROFILES:
                    emit("agent_start", {
                        "id": profile["id"],
                        "name": profile["name"],
                        "focus": profile["focus"],
                        "message": "Reading GBrain and checking contract paths.",
                    })
                    futures[executor.submit(_run_specialist_agent, profile, question, contracts)] = profile

                for future in as_completed(futures):
                    profile = futures[future]
                    try:
                        agent = future.result()
                    except Exception as exc:
                        agent = {
                            "id": profile["id"],
                            "name": profile["name"],
                            "focus": profile["focus"],
                            "available": False,
                            "memory": {"available": False, "output": ""},
                            "output": f"Agent failed: {exc}",
                            "raw_retrieved": "",
                        }
                    agents.append(agent)
                    emit(
                        "agent_done",
                        {k: v for k, v in agent.items() if k != "raw_retrieved"},
                    )

            order = {profile["id"]: index for index, profile in enumerate(AGENT_PROFILES)}
            agents = sorted(agents, key=lambda agent: order.get(agent["id"], 999))

            emit("status", {
                "stage": "validation",
                "message": "Checking that the recommended move can actually happen in the contract map.",
            })
            synthesis_result = _synthesize_agents(question, contracts, agents)
            answer = synthesis_result["answer"]
            emit("answer", {"answer": answer})

            primary_cid = list(_contracts.keys())[-1] if _contracts else None
            fsm_dict_snapshot = dict(_contracts[primary_cid]) if primary_cid else None

            emit("status", {
                "stage": "writeback",
                "message": "Saving this answer to shared memory.",
            })
            memory_write = _persist_agent_run(question, agents, answer, metrics=None)
            emit("memory_write", memory_write)

            emit("done", {
                "question": question,
                "answer": answer,
                "gbrain": gbrain,
                "agents": [
                    {k: v for k, v in agent.items() if k != "raw_retrieved"}
                    for agent in agents
                ],
                "memory_write": memory_write,
            })

            # MULTI-CONTRACT QUERIES: Metrics use the most recently uploaded
            # contract as ground truth. If a question spans several contracts,
            # scores may be computed against the wrong FSM until contract
            # selection is added.
            #
            # GBRAIN ABSENCE: If gbrain is unavailable, raw retrieved context is
            # empty. Context recall and precision default to 1.0 with zero totals
            # because there is no retrieval result to evaluate.
            #
            # METRICS NOT PERSISTED TO GBRAIN: _persist_agent_run() runs before
            # metrics complete. Persisting metrics requires a later ordering
            # refactor that waits for this background computation.
            def _emit_metrics():
                try:
                    if not primary_cid or fsm_dict_snapshot is None:
                        return

                    fsm_context_str = _build_fsm_context(
                        {primary_cid: fsm_dict_snapshot}
                    )
                    metrics_input = synthesis_result["metrics_input"]
                    faithfulness_result = compute_faithfulness(
                        synthesized_answer=synthesis_result["answer"],
                        fsm_context_str=fsm_context_str,
                        fsm_dict=fsm_dict_snapshot,
                    )
                    all_retrieved = "\n\n".join(
                        agent.get("raw_retrieved", "")
                        for agent in metrics_input["agent_results"]
                    )
                    recall_result = compute_context_recall(
                        question=question,
                        retrieved_chunks=all_retrieved,
                        fsm_dict=fsm_dict_snapshot,
                        fsm_context_str=fsm_context_str,
                    )
                    precision_result = compute_context_precision(
                        question=question,
                        retrieved_chunks_per_agent=metrics_input["retrieved_per_agent"],
                    )
                    metrics_payload = {
                        "faithfulness": faithfulness_result,
                        "context_recall": recall_result,
                        "context_precision": precision_result,
                    }
                    try:
                        emit("metrics", metrics_payload)
                    except BrokenPipeError:
                        pass
                except Exception as exc:
                    try:
                        emit("metrics_error", {"error": str(exc)})
                    except BrokenPipeError:
                        pass

            metrics_thread = threading.Thread(target=_emit_metrics, daemon=True)
            metrics_thread.start()
        except BrokenPipeError:
            return
        except Exception as exc:
            try:
                emit("server_error", {"error": str(exc)})
            except BrokenPipeError:
                return

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    global _contracts
    _clear_runtime_state()
    _contracts = _load_existing_fsms()
    gbrain = _sync_contracts_to_gbrain(_contracts)

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Babel: http://{args.host}:{args.port}")
    print(f"Started fresh with {len(_contracts)} uploaded contract(s).")
    print(f"GBrain: {gbrain.get('output', 'not synced').splitlines()[0]}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
