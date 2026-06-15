# SessionSubgraph — Rex + Sage loop as a LangGraph state machine.
#
# Flow (per docs/system-design.md state machine):
#
#   START
#     → coach_open
#     → rex_challenge        (challenge #1)
#     → evaluate_answer
#     → [conditional]  sage_depth  |  sage_explain
#     → [conditional]  cycle < max_cycles ? rex_rechallenge : coach_close
#                                  ↑
#     ←──────────────────  rex_rechallenge  (challenge #2, increments cycle)
#     → evaluate_answer
#     → [conditional]  sage_depth  |  sage_explain
#     → [conditional]  cycle >= max_cycles → coach_close
#     → END
#
# The two conditional edges are the *only* routing logic — no abstractions
# hiding the graph shape (per 2.3 learning objective).

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from nodes.coach_close import coach_close
from nodes.coach_open import coach_open
from nodes.evaluate_answer import evaluate_answer
from nodes.rex_challenge import rex_challenge
from nodes.rex_rechallenge import rex_rechallenge
from nodes.sage_respond import sage_depth, sage_explain
from state import AppState


def route_after_evaluation(state: AppState) -> str:
    """Conditional edge: correct → sage_depth, incorrect → sage_explain."""
    outcome = state.get("last_evaluation", {}).get("outcome")
    if outcome == "correct":
        return "sage_depth"
    return "sage_explain"


def route_after_sage(state: AppState) -> str:
    """Conditional edge: another cycle left → rex_rechallenge, else → coach_close."""
    cycle = state.get("cycle", 0)
    max_cycles = state.get("max_cycles", 2)
    if cycle < max_cycles:
        return "rex_rechallenge"
    return "coach_close"


def build_session_graph() -> StateGraph:
    """Compile the SessionSubgraph. Exposed as a factory so 2.4 can wrap it
    in a checkpointer without re-defining the structure."""
    graph = StateGraph(AppState)

    graph.add_node("coach_open", coach_open)
    graph.add_node("rex_challenge", rex_challenge)
    graph.add_node("evaluate_answer", evaluate_answer)
    graph.add_node("sage_depth", sage_depth)
    graph.add_node("sage_explain", sage_explain)
    graph.add_node("rex_rechallenge", rex_rechallenge)
    graph.add_node("coach_close", coach_close)

    graph.add_edge(START, "coach_open")
    graph.add_edge("coach_open", "rex_challenge")
    graph.add_edge("rex_challenge", "evaluate_answer")

    graph.add_conditional_edges(
        "evaluate_answer",
        route_after_evaluation,
        {"sage_depth": "sage_depth", "sage_explain": "sage_explain"},
    )

    # Both sage nodes converge to the cycle-end decision.
    graph.add_conditional_edges(
        "sage_depth",
        route_after_sage,
        {"rex_rechallenge": "rex_rechallenge", "coach_close": "coach_close"},
    )
    graph.add_conditional_edges(
        "sage_explain",
        route_after_sage,
        {"rex_rechallenge": "rex_rechallenge", "coach_close": "coach_close"},
    )

    # rex_rechallenge loops back to evaluate_answer with a fresh challenge.
    graph.add_edge("rex_rechallenge", "evaluate_answer")
    graph.add_edge("coach_close", END)

    return graph.compile()


# Module-level compiled graph for the FastAPI endpoint.
session_graph = build_session_graph()
