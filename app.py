#!/usr/bin/env python3
"""HTTP server for the Contract FSM Console — upload contracts, visualize FSMs, ask questions."""
from __future__ import annotations

import argparse
import json
import threading
from datetime import date
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent
UI_PATH = ROOT / "ui.html"
OUTPUT_DIR = ROOT / "output"


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


_contracts: dict[str, dict] = {}
_lock = threading.Lock()


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


def _gbrain_search(question: str, fsm_context: str = "") -> dict:
    """Step 1: Generate candidate suggestions informed by both FSM context and broad knowledge."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        fsm_section = f"\n\nContract FSM context:\n{fsm_context}" if fsm_context else ""
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=(
                "You are a knowledgeable business and financial advisor with expertise in contracts. "
                "You will be given a question and the relevant contract FSM data (states, transitions, rules). "
                "Generate a numbered list of concrete, actionable suggestions informed by both "
                "the contract structure and broader business/financial knowledge. "
                "Your suggestions should be grounded in what the contract describes — "
                "use the parties, amounts, states, and obligations as context for what options exist. "
                "Do not filter for feasibility yet; a strict FSM validation step follows."
            ),
            messages=[{"role": "user", "content": f"Question: {question}{fsm_section}"}],
        )
        output = msg.content[0].text
        return {"available": True, "output": output}
    except ImportError:
        return {"available": False, "output": "Anthropic SDK not available."}
    except Exception as exc:
        return {"available": False, "output": str(exc)}


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


def _ask_llm(question: str, contracts: dict[str, dict], gbrain_suggestions: str = "") -> str:
    """Step 2: Cross-reference GBrain suggestions against FSMs and return only feasible ones."""
    try:
        import anthropic
        client = anthropic.Anthropic()

        ctx = _build_fsm_context(contracts)

        if gbrain_suggestions:
            user_content = (
                f"Contract FSMs:\n\n{ctx}\n\n"
                f"---\n\n"
                f"GBrain candidate suggestions for: \"{question}\"\n\n"
                f"{gbrain_suggestions}\n\n"
                f"---\n\n"
                f"For each suggestion above, determine whether it is feasible given the contract FSMs. "
                f"A suggestion is feasible only if the required states, transitions, and rules exist "
                f"to support it playing out within the contract terms. "
                f"For feasible suggestions, cite the specific FSM states/transitions/rules that enable it. "
                f"For infeasible suggestions, explain which FSM constraint blocks it. "
                f"End with a clear recommendation of which option(s) to pursue and why."
            )
        else:
            user_content = f"Contract FSMs:\n\n{ctx}\n\nQuestion: {question}"

        system = (
            "You are a strict contract analyst. Your job is to validate suggestions against "
            "contract finite state machines. Never recommend an action that cannot be traced "
            "through the FSM's states, transitions, and rules. Be precise: cite FSM IDs. "
            "If no suggestions are feasible, say so plainly and explain why."
        )

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
        return msg.content[0].text
    except ImportError:
        return "Anthropic SDK not available. Install with: pip install anthropic"
    except Exception as exc:
        return f"Error querying LLM: {exc}"


class Handler(BaseHTTPRequestHandler):
    server_version = "ContractFSM/0.1"

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, indent=2, default=_json_default).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send_html(UI_PATH.read_text())
            return
        if path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
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

            self._send_json({"results": results})
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

            fsm_context = _build_fsm_context(contracts)
            gbrain = _gbrain_search(question, fsm_context)
            answer = _ask_llm(question, contracts, gbrain.get("output", ""))

            self._send_json({
                "question": question,
                "answer": answer,
                "gbrain": gbrain,
            })
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    global _contracts
    _contracts = _load_existing_fsms()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Contract FSM Console: http://{args.host}:{args.port}")
    print(f"Loaded {len(_contracts)} existing contract(s) from output/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
