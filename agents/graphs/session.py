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
#
# 2.4: the graph is compiled lazily, once, with the Postgres checkpointer
# wired in. State is persisted at every node boundary; thread_id identifies
# the session for resume.

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from db import get_checkpointer
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
    """Build the uncompiled StateGraph. Exposed as a factory so the structure
    is inspectable separately from the compiled runtime."""
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

    return graph


_cached_graph: "NodeAwareGraph" | None = None


class NodeAwareGraph:
    """Thin wrapper around CompiledStateGraph that supports ``invoke(input, node='name')``.

    When ``node`` is passed as a keyword argument, runs only that single node
    and returns the merged state dict — matching the test contract for
    task 9.3 integration tests.

    The wrapper is transparent for normal invocations (no ``node`` kwarg).
    """

    __slots__ = ("_graph",)

    def __init__(self, graph: CompiledStateGraph) -> None:
        object.__setattr__(self, "_graph", graph)

    def __getattr__(self, name: str):
        return getattr(self._graph, name)

    def __repr__(self) -> str:
        return f"NodeAwareGraph({self._graph!r})"

    def invoke(
        self,
        input: dict,
        config=None,
        *,
        node: str | None = None,
        **kwargs,
    ):
        if node is None:
            return self._graph.invoke(input, config, **kwargs)
        return _run_single_node(self._graph, node, input)

    async def ainvoke(self, input: dict, config=None, *, node: str | None = None, **kwargs):
        if node is None:
            return await self._graph.ainvoke(input, config, **kwargs)
        return await _arun_single_node(self._graph, node, input)


def _run_single_node(graph: CompiledStateGraph, node_name: str, state: dict) -> dict:
    """Run a single named node synchronously and return the merged state.

    Uses ainvoke internally since all session graph nodes are async.
    Always delegates to a fresh thread with its own event loop so that:
      - In sync contexts (plain pytest): no running loop → asyncio.run() works.
      - In async contexts (pytest-asyncio, nest_asyncio): avoids calling
        loop.run() on a potentially patched outer loop — no dependency on
        nest_asyncio monkey-patching for re-entrancy.
    """
    raw = graph.nodes[node_name]

    async def _invoke(s: dict) -> dict:
        if hasattr(raw, "ainvoke"):
            result = await raw.ainvoke(s)
        else:
            result = await raw.invoke(s)
        merged = dict(s)
        merged.update(result)
        return merged

    # Dedicated thread + ThreadPoolExecutor propagates exceptions cleanly
    # back to the calling thread without relying on nest_asyncio re-entrancy.
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, _invoke(state))
        return future.result()


async def _arun_single_node(graph: CompiledStateGraph, node_name: str, state: dict) -> dict:
    """Async version: run a single named node and return the merged state."""
    node_fn = graph.nodes[node_name].fn
    result = node_fn(state) if not asyncio.iscoroutinefunction(node_fn) else await node_fn(state)
    merged = dict(state)
    merged.update(result)
    return merged


def get_session_graph() -> NodeAwareGraph:
    """Lazily compile the graph with the Postgres checkpointer.
    First call wires it; subsequent calls return the cached instance."""
    global _cached_graph
    if _cached_graph is None:
        raw = build_session_graph().compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["evaluate_answer", "rex_rechallenge"]
        )
        _cached_graph = NodeAwareGraph(raw)
    return _cached_graph
