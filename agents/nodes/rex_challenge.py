# rex_challenge node — generates the first challenge for a session.
# Phase 1 logic ported from app/api/rex/challenge/route.ts.

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from prompts.rex import MODEL, build_rex_challenge_prompt
from state import AppState


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


def rex_challenge(state: AppState) -> dict:
    """Generate a DVA-C02 challenge for the current domain + difficulty."""
    system, user = build_rex_challenge_prompt(
        domain=state["current_domain"],
        topic=state.get("current_topic", ""),
        difficulty=state.get("rex_difficulty", "medium"),
    )

    llm = get_llm(MODEL)
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])

    raw = response.content if isinstance(response.content, str) else str(response.content)
    challenge = json.loads(_strip_code_fences(raw))

    if not all(k in challenge for k in ("domain", "topic", "scenario", "question")):
        raise ValueError(f"rex_challenge returned invalid shape: {challenge}")

    return {
        "current_challenge": {
            "domain": state["current_domain"],
            "topic": state.get("current_topic") or challenge["topic"],
            "scenario": challenge["scenario"],
            "question": challenge["question"],
        },
    }
