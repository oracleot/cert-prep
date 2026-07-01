# rex_challenge node — generates the first challenge for a session.
# Phase 1 logic ported from app/api/rex/challenge/route.ts.
#
# Phase 11: Rex is now option-based. The returned `current_challenge`
# carries `response_mode`, `options` (4 labeled A/B/C/D), and `answer_key`.
# See option_types for the labels and per-mode cardinality rules.

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from llm import get_llm, model_for
from option_types import (
    OPTION_LABELS,
    is_option_label,
    is_response_mode,
    max_labels_for_mode,
    normalize_option_labels,
)
from prompts.rex import MODEL, build_rex_challenge_prompt
from state import AppState


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


def _default_response_mode(state: AppState) -> str:
    """Phase 11 — app-controlled 60/40 single/multiple mix.

    The mix is approximated by cycling single/multi per prompt until enough
    sessions accumulate empirical telemetry; for V1 we bias single on odd
    cycles and multi on even cycles, which yields ~50/50 in a 2-cycle
    session and can be tuned later without a model swap. The full mix logic
    (per-session counters) lives in `session_mode_mix.py`; here we only
    need a per-prompt default when the route didn't pre-set one.
    """
    cycle = state.get("cycle", 1) or 1
    return "single_response" if cycle % 2 == 1 else "multiple_response"


def _normalize_options(raw: object) -> list[dict[str, str]]:
    """Coerce Rex's options list into the canonical shape.

    Tolerates missing/duplicated labels (we always emit exactly A/B/C/D in
    order), drops extra entries past D, and re-labels text by position so a
    shuffled Rex output still renders cleanly.
    """
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for idx, item in enumerate(raw[: len(OPTION_LABELS)]):
        label = OPTION_LABELS[idx]
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        out.append({"label": label, "text": text})
    while len(out) < len(OPTION_LABELS):
        # Pad so a malformed Rex payload still renders 4 rows; downstream
        # validation rejects this challenge, but the UI keeps a stable shape.
        out.append({"label": OPTION_LABELS[len(out)], "text": ""})
    return out


def _normalize_answer_key(raw: object, mode: str) -> list[str]:
    """Return a sorted, deduped list of valid labels matching the mode."""
    labels = normalize_option_labels(raw if isinstance(raw, list) else [])
    max_labels = max_labels_for_mode(mode)
    return labels[:max_labels]


def _validate_option_payload(challenge: dict, mode: str) -> None:
    """Hard-fail with a clear error if Rex drifted off the contract."""
    if not is_response_mode(mode):
        raise ValueError(f"rex_challenge returned invalid response_mode: {mode!r}")
    options = challenge.get("options")
    if not isinstance(options, list) or len(options) != 4:
        raise ValueError("rex_challenge must return exactly 4 options")
    labels_seen = [opt.get("label") for opt in options if isinstance(opt, dict)]
    if labels_seen != list(OPTION_LABELS):
        raise ValueError(f"rex_challenge option labels must be A/B/C/D in order; got {labels_seen}")
    if any(not (isinstance(opt, dict) and opt.get("text", "").strip()) for opt in options):
        raise ValueError("rex_challenge options must all have non-empty text")
    answer_key = challenge.get("answer_key")
    if not isinstance(answer_key, list) or not answer_key:
        raise ValueError("rex_challenge answer_key must be a non-empty list of labels")
    if not all(is_option_label(label) for label in answer_key):
        raise ValueError(f"rex_challenge answer_key contains invalid labels: {answer_key}")
    normalized = normalize_option_labels(answer_key)
    if len(normalized) != len(set(normalized)):
        raise ValueError("rex_challenge answer_key must not contain duplicates")
    max_labels = max_labels_for_mode(mode)
    if mode == "single_response" and len(normalized) != 1:
        raise ValueError(f"single_response answer_key must have exactly 1 label; got {normalized}")
    if mode == "multiple_response" and not (1 <= len(normalized) <= max_labels):
        raise ValueError(
            f"multiple_response answer_key must have 1-{max_labels} labels; got {normalized}"
        )


def rex_challenge(state: AppState, config: RunnableConfig) -> dict:
    """Generate a challenge for the current exam domain + difficulty.

    Phase 9.4 — Rex is grounded to the concept packet: ``facts`` and ``traps``
    are inlined into the prompt, and the returned ``topic`` is overwritten
    with the packet's topic so a free-roaming LLM cannot drift the challenge
    off-concept.

    Phase 11 — Rex returns an option-based challenge. The app picks the
    ``response_mode`` (defaulting to a 60/40 single/multiple mix in this
    node), and the prompt + parser enforce exactly 4 labeled A/B/C/D options
    with an answer_key of 1 (single) or 1-2 (multiple) labels.
    """
    packet_topic = state.get("current_topic", "") or ""
    response_mode = state.get("current_response_mode") or _default_response_mode(state)

    system, user = build_rex_challenge_prompt(
        exam_id=state["exam_id"],
        domain=state["current_domain"],
        topic=packet_topic,
        difficulty=state.get("rex_difficulty", "medium"),
        task_statement=state.get("current_task_statement", ""),
        services=state.get("current_services", []),
        source_ids=state.get("current_source_ids", []),
        concept_id=state.get("current_concept_id", ""),
        learning_style=state.get("learning_style", ""),
        familiarity_level=state.get("familiarity_level", "new"),
        facts=list(state.get("current_concept_facts", []) or []),
        traps=list(state.get("current_concept_traps", []) or []),
        response_mode=response_mode,
    )

    llm = get_llm(model_for("rex", MODEL))
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])

    raw = response.content if isinstance(response.content, str) else str(response.content)
    challenge = json.loads(_strip_code_fences(raw))

    if not all(k in challenge for k in ("domain", "topic", "scenario", "question")):
        raise ValueError(f"rex_challenge returned invalid shape: {challenge}")

    # Phase 11 — mode can drift from the app-set default if Rex echoes it
    # differently; trust the validated payload's mode, default to the
    # app-set value when missing.
    emitted_mode = challenge.get("response_mode")
    if not is_response_mode(emitted_mode):
        emitted_mode = response_mode

    # Validate the raw payload before normalization so a malformed Rex output
    # (3 options, bad labels, 2 correct labels on a single-response prompt)
    # hard-fails with a clear error rather than silently padding to fit.
    _validate_option_payload(
        {
            "options": challenge.get("options"),
            "answer_key": challenge.get("answer_key"),
        },
        emitted_mode,
    )
    challenge["response_mode"] = emitted_mode
    challenge["options"] = _normalize_options(challenge.get("options"))
    challenge["answer_key"] = _normalize_answer_key(challenge.get("answer_key"), emitted_mode)

    # Enforce packet grounding: if the LLM picked a topic outside the
    # selected concept, snap it back to the packet topic. concept_id is
    # always echoed verbatim so downstream nodes can detect drift.
    resolved_topic = packet_topic or challenge["topic"]

    return {
        "current_challenge": {
            "concept_id": state.get("current_concept_id", ""),
            "domain": state["current_domain"],
            "topic": resolved_topic,
            "topic_id": state.get("current_topic_id", ""),
            "task_statement_id": state.get("current_task_statement_id", ""),
            "task_statement": state.get("current_task_statement", ""),
            "difficulty": state.get("rex_difficulty", "medium"),
            "services": state.get("current_services", []),
            "source_ids": state.get("current_source_ids", []),
            "familiarity_level": state.get("familiarity_level", "new"),
            # Phase 9.5: forward the curated packet resources so Sage (and
            # the persisted exchange record) know which URLs are allowed.
            "official_docs": list(state.get("current_official_docs", []) or []),
            "skill_builder_links": list(state.get("current_skill_builder_links", []) or []),
            "lab_links": list(state.get("current_lab_links", []) or []),
            "expected_answer_criteria": state.get("current_expected_answer_criteria", "") or "",
            "traps": list(state.get("current_concept_traps", []) or []),
            "scenario": challenge["scenario"],
            "question": challenge["question"],
            # Phase 11 — option-based contract.
            "response_mode": emitted_mode,
            "options": challenge["options"],
            "answer_key": challenge["answer_key"],
        },
    }