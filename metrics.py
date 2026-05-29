"""
Evaluation metrics for the Babel RAG pipeline.

Three metrics:

  - compute_faithfulness(answer, fsm_context_str, fsm_dict) -> dict
  - compute_context_recall(question, retrieved_chunks, fsm_dict, fsm_context_str) -> dict
  - compute_context_precision(question, retrieved_chunks_per_agent) -> dict

All scores are floats in [0, 1] where 1 is best.
All LLM calls use model claude-sonnet-4-6 with max_tokens capped as noted.
"""

import json
import os
import re

import anthropic


MODEL = "claude-sonnet-4-6"
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def _iter_states(fsm_dict: dict) -> list[dict]:
    states = fsm_dict.get("states", [])
    if isinstance(states, dict):
        return [
            {"id": key, **value} if isinstance(value, dict) else {"id": key}
            for key, value in states.items()
        ]
    return [state for state in states if isinstance(state, dict)]


def _iter_transitions(fsm_dict: dict) -> list[dict]:
    transitions = fsm_dict.get("transitions", [])
    if isinstance(transitions, dict):
        return [
            {"id": key, **value} if isinstance(value, dict) else {"id": key}
            for key, value in transitions.items()
        ]
    return [transition for transition in transitions if isinstance(transition, dict)]


def _iter_rules(fsm_dict: dict) -> list[dict]:
    rules = fsm_dict.get("rules", [])
    if isinstance(rules, dict):
        return [
            {"id": key, **value} if isinstance(value, dict) else {"id": key}
            for key, value in rules.items()
        ]
    return [rule for rule in rules if isinstance(rule, dict)]


# ---------------------------------------------------------------------------
# METRIC 1: FAITHFULNESS
# ---------------------------------------------------------------------------

# Definition: fraction of atomic claims in the synthesized answer that are
# directly supported by the compiled FSM (states, transitions, rules, amounts).
#
# FAITHFULNESS LATENCY: Each atomic claim requires one LLM call in the fallback
# path. A 4-bullet answer with 2 claims per bullet produces up to 8 LLM calls.
# The background thread mitigates user-facing latency but increases total API
# cost per query.


def compute_faithfulness(
    synthesized_answer: str,
    fsm_context_str: str,
    fsm_dict: dict,
) -> dict:
    """
    Args:
        synthesized_answer: the final bullet-point answer from _synthesize_agents()
        fsm_context_str:    output of _build_fsm_context() as a plain text string
        fsm_dict:           the raw FSM dict from _contracts[cid], with keys:
                            "states", "transitions", "rules", "params"
    """
    claims = _extract_claims(synthesized_answer)

    if not claims:
        return {
            "score": 1.0,
            "total_claims": 0,
            "supported_claims": 0,
            "claims": [],
        }

    state_ids = {state.get("id", "") for state in _iter_states(fsm_dict) if state.get("id")}
    trigger_names = {
        (transition.get("trigger") or transition.get("event_type") or "").lower()
        for transition in _iter_transitions(fsm_dict)
        if transition.get("trigger") or transition.get("event_type")
    }
    fsm_amounts = _extract_fsm_amounts(fsm_dict)

    results = []
    supported = 0
    for claim in claims:
        prog = _programmatic_check(claim, state_ids, trigger_names, fsm_amounts)
        if prog is not None:
            results.append({
                "claim": claim,
                "supported": prog,
                "method": "programmatic",
            })
            if prog:
                supported += 1
        else:
            llm = _llm_faithfulness_check(claim, fsm_context_str)
            results.append({
                "claim": claim,
                "supported": llm,
                "method": "llm" if llm else "unsupported",
            })
            if llm:
                supported += 1

    score = supported / len(claims) if claims else 1.0

    return {
        "score": round(score, 4),
        "total_claims": len(claims),
        "supported_claims": supported,
        "claims": results,
    }


def _extract_claims(answer: str) -> list:
    """
    Use Claude to break the synthesized answer into atomic verifiable claims.
    Returns a list of claim strings. Falls back to line-splitting if the LLM
    call fails.
    """
    client = _get_client()
    prompt = (
        "Break the following answer into individual atomic claims. "
        "Each claim must be a single verifiable factual statement. "
        "Return ONLY a JSON array of strings, no markdown fences, "
        "no preamble, no other text.\n\n"
        f"Answer:\n{answer}"
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        return [claim for claim in parsed if isinstance(claim, str)]
    except Exception:
        lines = [
            line.strip().lstrip("-* ").strip()
            for line in answer.split("\n")
            if line.strip()
        ]
        return [line for line in lines if len(line) > 10]


def _extract_fsm_amounts(fsm_dict: dict) -> set:
    """
    Extract all numeric amounts from the FSM JSON and return them as normalized
    dollar strings and raw digit strings for flexible matching.
    """
    amounts = set()
    raw = json.dumps(fsm_dict)
    for num in re.findall(r"\b(\d+(?:\.\d+)?)\b", raw):
        try:
            val = float(num)
            amounts.add(f"${val:,.0f}")
            amounts.add(f"${val:,.2f}")
            amounts.add(str(int(val)))
        except ValueError:
            pass
    return amounts


def _programmatic_check(
    claim: str,
    state_ids: set,
    trigger_names: set,
    fsm_amounts: set,
):
    """
    Attempt to verify or refute a claim without an LLM call.
    Returns True, False, or None when inconclusive.
    """
    claim_lower = claim.lower()
    dollar_matches = re.findall(r"\$[\d,]+(?:\.\d+)?", claim)
    if dollar_matches:
        for match in dollar_matches:
            normalized = match
            try:
                val = float(match.replace("$", "").replace(",", ""))
                normalized = f"${val:,.0f}"
            except ValueError:
                pass
            if match in fsm_amounts or normalized in fsm_amounts:
                return True
        return False

    for state_id in state_ids:
        if state_id.lower().replace("_", " ") in claim_lower:
            return True

    for trigger in trigger_names:
        if trigger and trigger.replace("_", " ") in claim_lower:
            return True

    return None


def _llm_faithfulness_check(claim: str, fsm_context_str: str) -> bool:
    """
    Ask Claude whether a single claim is supported by the FSM context.
    Returns True if supported, False otherwise or on error.
    """
    client = _get_client()
    prompt = (
        "You are verifying whether a claim about a contract is supported "
        "by the contract's compiled state machine definition below.\n\n"
        f"FSM CONTEXT:\n{fsm_context_str[:3000]}\n\n"
        f"CLAIM: {claim}\n\n"
        "Is this claim directly supported by the FSM context? "
        "Reply with exactly one word: YES or NO."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip().upper().startswith("Y")
    except Exception:
        return False


# ---------------------------------------------------------------------------
# METRIC 2: CONTEXT RECALL
# ---------------------------------------------------------------------------

# Definition: fraction of FSM components needed to answer the question that
# were present in the GBrain-retrieved context.
#
# CONTEXT RECALL GROUND TRUTH IS APPROXIMATE: _extract_ground_truth_components()
# uses an LLM call to identify relevant FSM components. This may not enumerate
# all necessary components. For purely financial questions, supplement with
# executor output for exact ground truth.
#
# GBRAIN ABSENCE: If retrieved context is empty, recall defaults to 1.0 with
# total_components set to 0 because there is no retrieval result to evaluate.


def compute_context_recall(
    question: str,
    retrieved_chunks: str,
    fsm_dict: dict,
    fsm_context_str: str,
) -> dict:
    """
    Args:
        question:         the user's original question string
        retrieved_chunks: concatenated raw GBrain output across all agents
        fsm_dict:         the raw FSM dict
        fsm_context_str:  output of _build_fsm_context()
    """
    if not retrieved_chunks.strip():
        return {
            "score": 1.0,
            "total_components": 0,
            "recalled_components": 0,
            "missing_components": [],
            "note": "No retrieved context was available to evaluate.",
        }

    gt_components = _extract_ground_truth_components(
        question, fsm_dict, fsm_context_str
    )

    if not gt_components:
        return {
            "score": 1.0,
            "total_components": 0,
            "recalled_components": 0,
            "missing_components": [],
            "note": "No ground truth components identified for this question.",
        }

    retrieved_lower = retrieved_chunks.lower()
    recalled = []
    missing = []

    for component in gt_components:
        if _component_in_text(component, retrieved_lower):
            recalled.append(component)
        else:
            missing.append(component)

    score = len(recalled) / len(gt_components)

    return {
        "score": round(score, 4),
        "total_components": len(gt_components),
        "recalled_components": len(recalled),
        "missing_components": missing,
        "note": (
            "Low recall suggests GBrain keyword retrieval missed relevant "
            "clauses. Consider enabling --embed on gbrain import."
            if score < 0.5 else ""
        ),
    }


def _extract_ground_truth_components(
    question: str,
    fsm_dict: dict,
    fsm_context_str: str,
) -> list:
    """
    Build the full list of FSM components, then ask Claude which subset is
    relevant to this question. Falls back to all components up to 20.
    """
    client = _get_client()
    all_components = []

    for state in _iter_states(fsm_dict):
        state_id = state.get("id")
        if state_id:
            all_components.append(f"state:{state_id}")

    for transition in _iter_transitions(fsm_dict):
        transition_id = transition.get("id")
        event_type = transition.get("trigger") or transition.get("event_type")
        if transition_id:
            all_components.append(f"transition:{transition_id}")
        if event_type:
            all_components.append(f"event:{event_type}")

    for rule in _iter_rules(fsm_dict):
        if rule.get("id"):
            all_components.append(f"rule:{rule['id']}")
        for effect in rule.get("effects", []):
            if not isinstance(effect, dict):
                continue
            if effect.get("amount"):
                all_components.append(f"amount:{effect['amount']}")
            if effect.get("cap"):
                all_components.append(f"amount:{effect['cap']}")
            if effect.get("payment_formula"):
                all_components.append(f"formula:{effect['payment_formula']}")

    params = fsm_dict.get("params", {}) or {}
    for bucket in ("amounts", "rates", "durations", "thresholds"):
        values = params.get(bucket, {}) or {}
        if isinstance(values, dict):
            for key, value in values.items():
                all_components.append(f"{bucket}:{key}={value}")

    if not all_components:
        return []

    prompt = (
        "Given this question about a contract, identify which of the "
        "following FSM components are necessary to answer it correctly. "
        "Return ONLY a JSON array of the relevant component strings, "
        "no markdown fences, no preamble, no other text.\n\n"
        f"QUESTION: {question}\n\n"
        f"FSM CONTEXT:\n{fsm_context_str[:2000]}\n\n"
        f"COMPONENTS:\n{json.dumps(all_components[:300])}"
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        allowed = set(all_components)
        return [component for component in parsed if component in allowed]
    except Exception:
        return all_components[:20]


def _component_in_text(component: str, text_lower: str) -> bool:
    """
    Check whether a ground truth component string appears in retrieved text.
    """
    _, _, value = component.partition(":")
    if "=" in value:
        left, _, right = value.partition("=")
        candidates = [value, left, right]
    else:
        candidates = [value]

    for candidate in candidates:
        value_lower = candidate.lower().replace("_", " ")
        if value_lower and value_lower in text_lower:
            return True

        digits = re.sub(r"[^\d.]", "", candidate)
        if digits and digits in re.sub(r"[^\d.]", "", text_lower):
            return True

    return False


# ---------------------------------------------------------------------------
# METRIC 3: CONTEXT PRECISION
# ---------------------------------------------------------------------------

# Definition: fraction of retrieved GBrain chunks that were actually used by
# at least one agent when producing its answer.
#
# CONTEXT PRECISION CHUNK BOUNDARIES ARE HEURISTIC: Double-newline splitting
# works for the Markdown pages GBrain stores, but may merge or split logically
# distinct clauses if the FSM Markdown page is densely formatted.


def compute_context_precision(
    question: str,
    retrieved_chunks_per_agent: list,
) -> dict:
    """
    Args:
        retrieved_chunks_per_agent: list of dicts, one per agent.
    """
    total_chunks = 0
    total_relevant = 0
    per_agent_results = []

    for agent_data in retrieved_chunks_per_agent:
        agent_id = agent_data.get("agent_id", "unknown")
        retrieved = agent_data.get("retrieved", "")
        output = agent_data.get("agent_output", "")

        if not retrieved.strip():
            per_agent_results.append({
                "agent_id": agent_id,
                "chunks": 0,
                "relevant": 0,
                "precision": 1.0,
                "note": "No GBrain retrieval for this agent.",
            })
            continue

        chunks = [
            c.strip() for c in retrieved.split("\n\n")
            if c.strip() and len(c.strip()) > 20
        ]

        if not chunks:
            continue

        relevant_ids = _identify_relevant_chunks(
            question, chunks, output, agent_id
        )

        relevant_count = len(relevant_ids)
        precision = relevant_count / len(chunks) if chunks else 1.0
        total_chunks += len(chunks)
        total_relevant += relevant_count
        per_agent_results.append({
            "agent_id": agent_id,
            "chunks": len(chunks),
            "relevant": relevant_count,
            "precision": round(precision, 4),
        })

    overall_score = total_relevant / total_chunks if total_chunks > 0 else 1.0

    return {
        "score": round(overall_score, 4),
        "total_chunks": total_chunks,
        "relevant_chunks": total_relevant,
        "per_agent": per_agent_results,
    }


def _identify_relevant_chunks(
    question: str,
    chunks: list,
    agent_output: str,
    agent_id: str,
) -> list:
    """
    Ask Claude which chunk indices contributed to the agent's answer.
    Returns [] on any error.
    """
    client = _get_client()
    numbered = "\n\n".join(
        f"[{i}] {chunk}" for i, chunk in enumerate(chunks)
    )

    prompt = (
        f"You are evaluating a '{agent_id}' specialist agent's answer "
        f"to a contract question.\n\n"
        f"QUESTION: {question}\n\n"
        f"AGENT ANSWER:\n{agent_output}\n\n"
        f"RETRIEVED CONTEXT CHUNKS:\n{numbered[:3000]}\n\n"
        "Which chunk numbers (0-indexed) from the retrieved context "
        "contributed information that appears in the agent answer? "
        "Return ONLY a JSON array of integers, e.g. [0, 2]. "
        "Return [] if none were used. No markdown fences, no other text."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        indices = json.loads(raw)
        return [
            i for i in indices
            if isinstance(i, int) and 0 <= i < len(chunks)
        ]
    except Exception:
        return []
