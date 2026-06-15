# rex_rechallenge node — generates a harder variant on the same domain.
# Phase 1 logic ported from app/api/rex/rechallenge/route.ts.

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from prompts.rex import MODEL, build_rex_rechallenge_prompt
from state import AppState


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


def rex_rechallenge(state: AppState) -> dict:
    """Generate a harder challenge on the same domain, increment the cycle."""
    system, user = build_rex_rechallenge_prompt(
        domain=state["current_domain"],
        previous_topic=state["current_challenge"]["topic"],
        difficulty="hard",
    )

    llm = get_llm(MODEL)
    response = llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)],
        temperature=0.8,
        max_tokens=512,
    )

    raw = response.content if isinstance(response.content, str) else str(response.content)
    challenge = json.loads(_strip_code_fences(raw))

    if not all(k in challenge for k in ("domain", "topic", "scenario", "question")):
        raise ValueError(f"rex_rechallenge returned invalid shape: {challenge}")

    return {
        "current_challenge": {
            "domain": challenge["domain"],
            "topic": challenge["topic"],
            "scenario": challenge["scenario"],
            "question": challenge["question"],
        },
        "cycle": state.get("cycle", 1) + 1,
    }
