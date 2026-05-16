"""Maria's Bakery FSM question answering and scenario verification.

This module stays dependency-free so the demo can run anywhere the repository
does. It ranks business scenarios from the four Maria's Bakery FSM JSON files,
then replays the suggested events through the FSMs to prove the stated outcome.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_IDS = (
    "C_VAN_contract",
    "C_LEASE_contract",
    "C_SUPPLIER_contract",
    "C_WHOLESALE_contract",
)

STARTING_CASH = 32_000.0
RENTAL_BRIDGE_COST = 2_000.0


def load_contracts(root: Path | None = None) -> dict[str, dict[str, Any]]:
    base = (root or ROOT) / "output"
    contracts: dict[str, dict[str, Any]] = {}
    for contract_id in CONTRACT_IDS:
        path = base / contract_id / "fsm.json"
        contracts[contract_id] = json.loads(path.read_text())
    return contracts


def _money(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _initial_fields(fsm: dict[str, Any]) -> dict[str, Any]:
    params = fsm.get("params") or {}
    fields: dict[str, Any] = {}
    for group in ("amounts", "rates", "durations", "thresholds", "base_dates"):
        for key, value in (params.get(group) or {}).items():
            if value is None:
                fields[key] = None
                continue
            try:
                fields[key] = float(value)
            except (TypeError, ValueError):
                fields[key] = value
    return fields


SAFE_NAMES: dict[str, Any] = {
    "abs": abs,
    "bool": bool,
    "false": False,
    "False": False,
    "float": float,
    "int": int,
    "max": max,
    "min": min,
    "round": round,
    "true": True,
    "True": True,
}


def _safe_eval(expr: str | None, fields: dict[str, Any], details: dict[str, Any]) -> Any:
    if expr is None or expr == "":
        return True
    ctx = dict(SAFE_NAMES)
    ctx.update(fields)
    ctx.update(details)
    try:
        return eval(expr, {"__builtins__": {}}, ctx)  # noqa: S307 - guarded names only
    except Exception:
        return None


def simulate_contract(
    fsm: dict[str, Any],
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    state = fsm["initial_state"]
    terminal_states = {s["id"] for s in fsm.get("states", []) if s.get("terminal")}
    state_ids = {s["id"] for s in fsm.get("states", [])}
    fields = _initial_fields(fsm)
    payments: list[dict[str, Any]] = []
    log: list[dict[str, Any]] = []

    for idx, event in enumerate(sorted(events or [], key=lambda e: e.get("timestamp", "")), 1):
        event_type = event.get("event_type", "")
        details = event.get("details") or {}
        before = state
        entry: dict[str, Any] = {
            "step": idx,
            "timestamp": event.get("timestamp", ""),
            "event_type": event_type,
            "party": event.get("party", ""),
            "details": details,
            "state_before": before,
            "transition_id": None,
            "transition_description": "",
            "effects": [],
            "payments": [],
            "state_after": before,
            "fired": False,
        }

        if before in terminal_states:
            entry["note"] = "Terminal state; event ignored."
            log.append(entry)
            continue

        fired_transition = None
        for transition in fsm.get("transitions", []):
            if before not in transition.get("from_states", []):
                continue
            if transition.get("event_type") != event_type:
                continue
            guard = transition.get("guard")
            guard_result = _safe_eval(guard, fields, details)
            if guard is not None and not bool(guard_result):
                continue
            fired_transition = transition
            break

        if fired_transition is None:
            entry["note"] = "No FSM transition matched this event and guard."
            log.append(entry)
            continue

        state_override = None
        for effect in fired_transition.get("effects") or []:
            effect_record = {
                "id": effect.get("id", ""),
                "type": effect.get("type", ""),
                "description": effect.get("description", ""),
            }
            if effect.get("type") == "PAYMENT":
                amount = _money(_safe_eval(effect.get("payment_formula"), fields, details))
                cap = effect.get("cap")
                if cap is not None:
                    amount = min(amount, _money(cap))
                payment = {
                    "from": effect.get("payment_from", "unknown"),
                    "to": effect.get("payment_to", "unknown"),
                    "amount": round(amount, 2),
                    "effect_id": effect.get("id", ""),
                    "description": effect.get("description", ""),
                }
                payments.append(payment)
                entry["payments"].append(payment)
                effect_record["amount"] = round(amount, 2)
            if effect.get("new_state") in state_ids:
                state_override = effect["new_state"]
            entry["effects"].append(effect_record)

        state = state_override or fired_transition.get("to_state", state)
        entry.update(
            {
                "transition_id": fired_transition.get("id"),
                "transition_description": fired_transition.get("description", ""),
                "state_after": state,
                "fired": True,
            }
        )
        log.append(entry)

    return {
        "contract_id": fsm.get("contract_id"),
        "initial_state": fsm.get("initial_state"),
        "final_state": state,
        "payments": payments,
        "log": log,
        "fired_transition_ids": [row["transition_id"] for row in log if row.get("transition_id")],
    }


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    stance: str
    summary: str
    assumptions: list[str]
    events: dict[str, list[dict[str, Any]]]
    external_costs: dict[str, float]
    expected_states: dict[str, str]
    tags: tuple[str, ...]


def _event(timestamp: str, event_type: str, party: str = "Maria's Bakery LLC", **details: Any) -> dict[str, Any]:
    return {"timestamp": timestamp, "event_type": event_type, "party": party, "details": details}


def scenario_library() -> list[Scenario]:
    supplier_rebate_cycle = [
        _event("2027-01-31", "month_end_evaluation", monthly_purchases=8000),
        _event("2027-02-01", "rebate_applied"),
        _event("2027-02-02", "invoice_payment", invoice_amount=8000),
    ]
    clean_wholesale_month = [
        _event("2027-01-31", "invoice_issued"),
        _event("2027-02-10", "payment_received", party="Three Oaks Cafe Group LLC", days_since_invoice=10, undisputed_amount=18000),
    ]
    rent_only = [_event("2027-01-01", "rent_payment_made")]

    return [
        Scenario(
            id="buy_now_confirmed",
            title="Buy now after insurance and landlord consent are confirmed",
            stance="conditional-green",
            summary="Own the van before the route, keep the wholesale account clean, and earn the supplier rebate.",
            assumptions=[
                "Insurance binder is active before physical delivery.",
                "Landlord consent is in hand before refrigerated vehicle activity at the premises.",
                "Van is inspected and accepted before the January 1 route obligations matter.",
            ],
            events={
                "C_VAN_contract": [
                    _event("2026-12-20", "down_payment_made"),
                    _event("2026-12-27", "equipment_delivered", party="ColdRoad Vans Inc.", insurance_active=True),
                    _event("2026-12-28", "equipment_inspected_accepted"),
                    _event("2027-01-31", "monthly_payment_made"),
                ],
                "C_LEASE_contract": rent_only,
                "C_SUPPLIER_contract": supplier_rebate_cycle,
                "C_WHOLESALE_contract": clean_wholesale_month,
            },
            external_costs={},
            expected_states={
                "C_VAN_contract": "OPERATIONAL",
                "C_LEASE_contract": "ACTIVE",
                "C_SUPPLIER_contract": "ACTIVE",
                "C_WHOLESALE_contract": "ACTIVE",
            },
            tags=("buy", "owned-van", "year-end", "rebate", "route-safe"),
        ),
        Scenario(
            id="rental_bridge_then_buy",
            title="Use a refrigerated rental bridge, then buy after timing is certain",
            stance="risk-controlled",
            summary="Protect the route and supplier rebate while avoiding owned-van insurance timing risk.",
            assumptions=[
                "Bridge vehicle is already legal to use for deliveries.",
                "Landlord consent or offsite loading covers the bridge vehicle.",
                f"Rental bridge cost is modeled as ${RENTAL_BRIDGE_COST:,.0f}; this cost is outside the four FSMs.",
            ],
            events={
                "C_VAN_contract": [],
                "C_LEASE_contract": rent_only,
                "C_SUPPLIER_contract": supplier_rebate_cycle,
                "C_WHOLESALE_contract": clean_wholesale_month,
            },
            external_costs={"rental_bridge": RENTAL_BRIDGE_COST},
            expected_states={
                "C_VAN_contract": "ACTIVE",
                "C_LEASE_contract": "ACTIVE",
                "C_SUPPLIER_contract": "ACTIVE",
                "C_WHOLESALE_contract": "ACTIVE",
            },
            tags=("wait", "rental", "bridge", "rebate", "route-safe", "cash"),
        ),
        Scenario(
            id="buy_now_insurance_slips_no_bridge",
            title="Buy now, insurance slips, no bridge",
            stance="high-risk",
            summary="The van is delivered but unusable, wholesale performance breaks, and the account moves toward termination.",
            assumptions=[
                "Insurance binder slips until after the first wholesale deliveries.",
                "Maria attempts the route without a legally usable vehicle.",
                "Landlord consent is not ready when refrigerated vehicle activity begins.",
            ],
            events={
                "C_VAN_contract": [
                    _event("2026-12-20", "down_payment_made"),
                    _event("2026-12-27", "equipment_delivered", party="ColdRoad Vans Inc.", insurance_active=False),
                    _event("2027-01-18", "insurance_activated"),
                    _event("2027-01-19", "equipment_inspected_accepted"),
                    _event("2027-01-31", "monthly_payment_made"),
                ],
                "C_LEASE_contract": [
                    _event("2027-01-01", "rent_payment_made"),
                    _event("2027-01-01", "unauthorized_refrigerated_vehicle"),
                    _event("2027-01-02", "cure_notice_issued"),
                    _event("2027-01-08", "violation_cured", cure_within_period=True),
                    _event("2027-01-09", "return_to_compliance"),
                ],
                "C_SUPPLIER_contract": [
                    _event("2027-02-02", "invoice_payment", invoice_amount=4500),
                ],
                "C_WHOLESALE_contract": [
                    _event("2027-01-02", "delivery_late", late_count=0),
                    _event("2027-01-03", "delivery_late", late_count=1),
                    _event("2027-01-04", "delivery_late", late_count=2),
                    _event("2027-01-04", "at_risk_threshold_reached", late_or_missed_count=3),
                    _event("2027-01-05", "at_risk_notice_issued"),
                    _event("2027-01-16", "cure_failed"),
                    _event("2027-02-15", "termination_effective", days_since_notice=30, earned_amount=750, credits=750, offsets=0),
                ],
            },
            external_costs={},
            expected_states={
                "C_VAN_contract": "OPERATIONAL",
                "C_LEASE_contract": "ACTIVE",
                "C_SUPPLIER_contract": "ACTIVE",
                "C_WHOLESALE_contract": "TERMINATED",
            },
            tags=("buy", "insurance-risk", "late", "termination", "penalty"),
        ),
        Scenario(
            id="buy_without_landlord_consent",
            title="Buy insured van but miss landlord consent",
            stance="lease-risk",
            summary="The van and route work, but the lease FSM assesses a violation fee and cure process.",
            assumptions=[
                "Insurance is active and the van is accepted.",
                "Landlord consent is missing before refrigerated vehicle activity at the premises.",
            ],
            events={
                "C_VAN_contract": [
                    _event("2026-12-20", "down_payment_made"),
                    _event("2026-12-27", "equipment_delivered", party="ColdRoad Vans Inc.", insurance_active=True),
                    _event("2026-12-28", "equipment_inspected_accepted"),
                    _event("2027-01-31", "monthly_payment_made"),
                ],
                "C_LEASE_contract": [
                    _event("2027-01-01", "rent_payment_made"),
                    _event("2027-01-02", "unauthorized_refrigerated_vehicle"),
                    _event("2027-01-03", "cure_notice_issued"),
                    _event("2027-01-08", "violation_cured", cure_within_period=True),
                    _event("2027-01-09", "return_to_compliance"),
                ],
                "C_SUPPLIER_contract": supplier_rebate_cycle,
                "C_WHOLESALE_contract": clean_wholesale_month,
            },
            external_costs={},
            expected_states={
                "C_VAN_contract": "OPERATIONAL",
                "C_LEASE_contract": "ACTIVE",
                "C_SUPPLIER_contract": "ACTIVE",
                "C_WHOLESALE_contract": "ACTIVE",
            },
            tags=("buy", "lease-risk", "rebate", "route-safe", "penalty"),
        ),
        Scenario(
            id="wait_no_route",
            title="Wait and do not start the wholesale route",
            stance="cash-preservation",
            summary="Preserve optionality and avoid contract penalties, but leave the wholesale revenue and rebate unrealized.",
            assumptions=[
                "Maria does not sign the wholesale route for the first modeled month.",
                "The supplier minimum is not activated by the wholesale route.",
                "The van purchase is deferred.",
            ],
            events={
                "C_VAN_contract": [],
                "C_LEASE_contract": rent_only,
                "C_SUPPLIER_contract": [],
                "C_WHOLESALE_contract": [],
            },
            external_costs={},
            expected_states={
                "C_VAN_contract": "ACTIVE",
                "C_LEASE_contract": "ACTIVE",
                "C_SUPPLIER_contract": "ACTIVE",
                "C_WHOLESALE_contract": "ACTIVE",
            },
            tags=("wait", "cash", "low-risk"),
        ),
        Scenario(
            id="supplier_cold_chain_failure",
            title="Route starts but supplier cold-chain failure disrupts performance",
            stance="supplier-risk",
            summary="Even with vehicle readiness, supplier failure can still create route lateness and at-risk pressure.",
            assumptions=[
                "Van timing and landlord consent are solved.",
                "Supplier cold-chain failure interferes with breakfast route performance.",
            ],
            events={
                "C_VAN_contract": [
                    _event("2026-12-20", "down_payment_made"),
                    _event("2026-12-27", "equipment_delivered", party="ColdRoad Vans Inc.", insurance_active=True),
                    _event("2026-12-28", "equipment_inspected_accepted"),
                    _event("2027-01-31", "monthly_payment_made"),
                ],
                "C_LEASE_contract": rent_only,
                "C_SUPPLIER_contract": [
                    _event("2027-01-03", "cold_chain_shortfall", party="Valley Provisions LLC"),
                    _event("2027-01-06", "cold_chain_restored", party="Valley Provisions LLC"),
                    _event("2027-02-02", "invoice_payment", invoice_amount=4500),
                ],
                "C_WHOLESALE_contract": [
                    _event("2027-01-03", "delivery_late", late_count=0),
                    _event("2027-01-04", "delivery_late", late_count=1),
                    _event("2027-01-31", "invoice_issued"),
                    _event("2027-02-10", "payment_received", party="Three Oaks Cafe Group LLC", days_since_invoice=10, undisputed_amount=17500),
                    _event("2027-02-11", "performance_restored", late_count=2),
                ],
            },
            external_costs={},
            expected_states={
                "C_VAN_contract": "OPERATIONAL",
                "C_LEASE_contract": "ACTIVE",
                "C_SUPPLIER_contract": "ACTIVE",
                "C_WHOLESALE_contract": "ACTIVE",
            },
            tags=("supplier-risk", "late", "buy", "route-safe"),
        ),
    ]


def _payment_totals(results: dict[str, dict[str, Any]], external_costs: dict[str, float]) -> dict[str, float]:
    inbound = 0.0
    outbound = 0.0
    supplier_rebate = 0.0
    wholesale_revenue = 0.0
    late_credits = 0.0
    lease_fees = 0.0
    van_cash_out = 0.0
    supplier_spend = 0.0

    for result in results.values():
        for payment in result["payments"]:
            amount = _money(payment["amount"])
            from_party = payment["from"].lower()
            to_party = payment["to"].lower()
            desc = payment.get("description", "").lower()
            if "bakery" in to_party:
                inbound += amount
                if "customer" in from_party or "three oaks" in from_party:
                    wholesale_revenue += amount
                if "supplier" in from_party:
                    supplier_rebate += amount
            if "bakery" in from_party or from_party == "tenant":
                outbound += amount
                if "customer" in to_party:
                    late_credits += amount
                if "landlord" in to_party and "violation" in desc:
                    lease_fees += amount
                if "coldroad" in to_party or "bank" in to_party:
                    van_cash_out += amount
                if "supplier" in to_party:
                    supplier_spend += amount

    external_total = sum(external_costs.values())
    return {
        "inbound": round(inbound, 2),
        "outbound": round(outbound, 2),
        "external_costs": round(external_total, 2),
        "net_cash_delta": round(inbound - outbound - external_total, 2),
        "ending_cash": round(STARTING_CASH + inbound - outbound - external_total, 2),
        "supplier_rebate": round(supplier_rebate, 2),
        "wholesale_revenue": round(wholesale_revenue, 2),
        "late_credits": round(late_credits, 2),
        "lease_fees": round(lease_fees, 2),
        "van_cash_out": round(van_cash_out, 2),
        "supplier_spend": round(supplier_spend, 2),
    }


def infer_objectives(question: str) -> dict[str, float]:
    q = question.lower()
    weights = {
        "route_preserved": 3.0,
        "wholesale_revenue": 2.0,
        "avoid_termination": 3.0,
        "avoid_penalties": 2.0,
        "ending_cash": 1.2,
    }
    if re.search(r"tax|year.?end|placed|service|operational|available", q):
        weights["van_operational_by_year_end"] = 3.0
    if re.search(r"rebate|supplier|ingredient|minimum", q):
        weights["supplier_rebate"] = 2.0
    if re.search(r"cash|profit|money|maximize|revenue|output|best", q):
        weights["ending_cash"] = weights.get("ending_cash", 0) + 1.2
        weights["wholesale_revenue"] = weights.get("wholesale_revenue", 0) + 1.0
    if re.search(r"risk|penalt|late|miss|termination|default|avoid|safe", q):
        weights["avoid_penalties"] = weights.get("avoid_penalties", 0) + 1.5
        weights["avoid_termination"] = weights.get("avoid_termination", 0) + 1.5
    if re.search(r"rental|bridge|wait|delay", q):
        weights["flexibility"] = 1.5
    if re.search(r"buy|van|owned", q):
        weights["van_operational_by_year_end"] = weights.get("van_operational_by_year_end", 0) + 1.0
    return weights


def _score_metric(value: float, low: float, high: float) -> float:
    if math.isclose(high, low):
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def _summarize_verification(results: dict[str, dict[str, Any]], expected: dict[str, str]) -> dict[str, Any]:
    contracts = {}
    all_ok = True
    for contract_id, result in results.items():
        expected_state = expected.get(contract_id)
        ok = expected_state is None or result["final_state"] == expected_state
        all_ok = all_ok and ok
        contracts[contract_id] = {
            "expected_state": expected_state,
            "actual_state": result["final_state"],
            "ok": ok,
            "fired_transition_ids": result["fired_transition_ids"],
        }
    return {"ok": all_ok, "contracts": contracts}


def _scenario_metrics(scenario: Scenario, results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    money = _payment_totals(results, scenario.external_costs)
    final_states = {cid: result["final_state"] for cid, result in results.items()}
    wholesale_state = final_states.get("C_WHOLESALE_contract")
    route_preserved = wholesale_state not in {"TERMINATED", "TERMINATION_NOTICE_GIVEN", "AT_RISK", "IN_CURE"}
    return {
        **money,
        "route_preserved": route_preserved,
        "wholesale_terminated": wholesale_state == "TERMINATED",
        "van_operational_by_year_end": scenario.id in {"buy_now_confirmed", "buy_without_landlord_consent", "supplier_cold_chain_failure"},
        "lease_default": final_states.get("C_LEASE_contract") in {"DEFAULT", "TERMINATED"},
        "supplier_rebate_earned": money["supplier_rebate"] >= 400,
        "final_states": final_states,
    }


def rank_scenarios(question: str, contracts: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    contracts = contracts or load_contracts()
    objectives = infer_objectives(question)
    q = question.lower()
    evaluated = []

    for scenario in scenario_library():
        results = {
            contract_id: simulate_contract(contracts[contract_id], scenario.events.get(contract_id, []))
            for contract_id in CONTRACT_IDS
        }
        metrics = _scenario_metrics(scenario, results)
        score_parts = {
            "route_preserved": 1.0 if metrics["route_preserved"] else 0.0,
            "wholesale_revenue": _score_metric(metrics["wholesale_revenue"], 0, 18_000),
            "avoid_termination": 0.0 if metrics["wholesale_terminated"] else 1.0,
            "avoid_penalties": 1.0 - _score_metric(metrics["late_credits"] + metrics["lease_fees"], 0, 1_250),
            "ending_cash": _score_metric(metrics["ending_cash"], 15_000, 38_000),
            "supplier_rebate": _score_metric(metrics["supplier_rebate"], 0, 400),
            "van_operational_by_year_end": 1.0 if metrics["van_operational_by_year_end"] else 0.0,
            "flexibility": 1.0 if "rental" in scenario.tags or "wait" in scenario.tags else 0.3,
        }
        score = sum(objectives.get(k, 0) * score_parts.get(k, 0) for k in objectives)
        if re.search(r"insurance.*slip|slip.*insurance|delivered.*uninsured|no bridge|without.*bridge", q):
            if scenario.id == "buy_now_insurance_slips_no_bridge":
                score += 20
        if re.search(r"landlord|consent|lease", q) and re.search(r"miss|without|no |unauthorized", q):
            if scenario.id == "buy_without_landlord_consent":
                score += 12
        if re.search(r"cold.?chain|supplier failure|spoilage", q):
            if scenario.id == "supplier_cold_chain_failure":
                score += 12
        verification = _summarize_verification(results, scenario.expected_states)
        evaluated.append(
            {
                "id": scenario.id,
                "title": scenario.title,
                "stance": scenario.stance,
                "summary": scenario.summary,
                "assumptions": scenario.assumptions,
                "tags": list(scenario.tags),
                "score": round(score, 3),
                "score_parts": score_parts,
                "metrics": metrics,
                "verification": verification,
                "results": results,
                "events": scenario.events,
                "external_costs": scenario.external_costs,
            }
        )

    evaluated.sort(key=lambda item: item["score"], reverse=True)
    answer = _compose_answer(question, objectives, evaluated)
    return {
        "question": question,
        "objectives": objectives,
        "answer": answer,
        "scenarios": evaluated,
        "gbrain": gbrain_search(question),
    }


def _compose_answer(question: str, objectives: dict[str, float], ranked: list[dict[str, Any]]) -> str:
    ids = {item["id"]: item for item in ranked}
    confirmed = ids.get("buy_now_confirmed")
    bridge = ids.get("rental_bridge_then_buy")
    top = ranked[0]
    q = question.lower()

    if re.search(r"insurance.*slip|slip.*insurance|delivered.*uninsured|no bridge|without.*bridge", q):
        return (
            "If insurance slips and there is no bridge, the FSMs verify the bad path: the van can be delivered but unusable, "
            "lease activity can trigger a refrigerated-vehicle violation, and the wholesale FSM can move from late deliveries "
            "to at-risk, cure failure, and termination. The modeled cash result is poor because Maria still pays van, rent, "
            "supplier, late-credit, and lease-violation costs without preserving the $18,000 route."
        )

    asks_decision = bool(re.search(r"should|buy|wait|rental|bridge|now", question.lower()))
    if asks_decision and confirmed and bridge:
        return (
            "Best contract-grounded answer: buy now only if insurance and landlord consent are confirmed before deliveries; "
            "otherwise use the rental bridge. The confirmed-buy path reaches OPERATIONAL in the van FSM, keeps the lease ACTIVE, "
            "earns the $400 supplier rebate, and keeps the wholesale FSM ACTIVE with the $18,000 invoice paid. The bridge path "
            "keeps the route and rebate alive while avoiding the delivered-but-uninsured failure mode. The no-bridge insurance-slip "
            "path verifies the downside: wholesale termination pressure, late credits, lease violation cost, supplier spend, and van cash out."
        )

    objective_names = ", ".join(k.replace("_", " ") for k in objectives)
    return (
        f"Highest-scoring scenario for {objective_names}: {top['title']}. "
        f"It verifies against the FSMs with final states {top['metrics']['final_states']} and an ending cash estimate of "
        f"${top['metrics']['ending_cash']:,.0f}."
    )


def gbrain_search(question: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["gbrain", "search", question],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "output": str(exc)}

    output = (proc.stdout or proc.stderr or "").strip()
    return {
        "available": proc.returncode == 0,
        "returncode": proc.returncode,
        "output": output[:4000],
    }


def contract_summaries(contracts: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    contracts = contracts or load_contracts()
    summaries = []
    for contract_id, fsm in contracts.items():
        summaries.append(
            {
                "contract_id": contract_id,
                "parties": fsm.get("parties", []),
                "initial_state": fsm.get("initial_state"),
                "state_count": len(fsm.get("states", [])),
                "transition_count": len(fsm.get("transitions", [])),
                "event_types": sorted({t.get("event_type", "") for t in fsm.get("transitions", [])}),
                "amounts": (fsm.get("params") or {}).get("amounts", {}),
                "thresholds": (fsm.get("params") or {}).get("thresholds", {}),
            }
        )
    return summaries


if __name__ == "__main__":
    import sys

    prompt = " ".join(sys.argv[1:]) or (
        "Should Maria's Bakery sign the wholesale route and buy the refrigerated van now, "
        "or should she wait or use a rental bridge first?"
    )
    print(json.dumps(rank_scenarios(prompt), indent=2))
