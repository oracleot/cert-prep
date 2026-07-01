"""Phase 11 — SSE event generator for ``POST /session/submit``.

Extracted from ``routes/session.py`` so the route file stays under the
200-line hard rule. Consumes LangGraph ``astream_events`` and emits:

    - ``evaluation`` : the full ``last_evaluation`` dict (Phase 11 also
      includes chosen / correct / missed / incorrect labels for option
      prompts) so the UI can render the verdict overlay before Sage streams.
    - ``token``      : incremental Sage stream chunks.
    - ``citations``  : the Sage citation set after the cycle ends.
    - ``done``       : session stream completed (always last, after the
                       ``astream_events`` loop drains so a trailing node
                       end can never slip past the client contract).
    - ``error``      : surfaced to the client with the original message.

The generator is an async iterator (``AsyncIterator[str]``) so FastAPI's
``StreamingResponse`` can consume it directly.
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator


async def submit_sse_generator(
    graph,
    config,
    *,
    api_key: str,
    model_overrides: dict[str, str] | None = None,
) -> AsyncIterator[str]:
    """Yield SSE event strings for the duration of a submit cycle.

    The ``graph`` argument is the LangGraph ``CompiledStateGraph`` (or our
    ``NodeAwareGraph`` wrapper). The caller is responsible for running
    ``ainvoke(None)`` via the graph in the surrounding route — this function
    only consumes events for the already-invoked submit.

    Event ordering is guaranteed as
    ``evaluation → token* → citations → done`` (or ``→ error`` on
    failure). ``done`` is emitted after the ``astream_events`` iterator
    drains so a late ``on_chain_end`` from a nested tool / sub-graph
    cannot fire a trailing event after the client has already closed
    out the cycle.
    """
    from llm import llm_runtime  # local import: avoids circular at module load

    try:
        with llm_runtime(api_key, model_overrides or {}):
            async for event in graph.astream_events(None, config=config, version="v2"):
                kind = event["event"]
                name = event["name"]
                if kind == "on_chat_model_stream":
                    node = event.get("metadata", {}).get("langgraph_node")
                    if node in {"sage_depth", "sage_explain"}:
                        chunk = event["data"].get("chunk")
                        if chunk and hasattr(chunk, "content") and chunk.content:
                            yield f"data: {json.dumps({'type': 'token', 'token': chunk.content})}\n\n"
                elif kind == "on_chain_end" and name == "evaluate_answer":
                    out = event["data"].get("output")
                    if out and "last_evaluation" in out:
                        yield f"data: {json.dumps({'type': 'evaluation', 'data': json.dumps(out['last_evaluation'])})}\n\n"
                elif kind == "on_chain_end" and name in {"sage_depth", "sage_explain"}:
                    out = event["data"].get("output") or {}
                    h = out.get("session_history") or []
                    if h:
                        yield f"data: {json.dumps({'type': 'citations', 'data': h[-1].get('citations', [])})}\n\n"
        # ``done`` is the last event the client sees; emit it after the
        # astream_events loop drains so no node-end event can fire after.
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'error': {'message': str(exc)}})}\n\n"


__all__ = ["submit_sse_generator"]