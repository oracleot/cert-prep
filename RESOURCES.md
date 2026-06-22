# Rex/Sage LangGraph Resources

## Knowledge

- [Repo: `agents/graphs/session.py`](agents/graphs/session.py)
  Primary source for the Rex/Sage LangGraph state machine: nodes, edges, conditional routing, interrupts, and checkpointer compilation.
- [Repo: `agents/state.py`](agents/state.py)
  Primary source for the shared `AppState` contract every graph node reads from and writes to.
- [Repo: `agents/nodes/rex_challenge.py`](agents/nodes/rex_challenge.py)
  Shows Rex as a LangGraph node that calls a LangChain chat model and returns a state patch.
- [Repo: `agents/nodes/sage_respond.py`](agents/nodes/sage_respond.py)
  Shows Sage split into two graph nodes: one for depth after a correct answer and one for repair after an incorrect answer.
- [LangGraph docs: Graphs](https://langchain-ai.github.io/langgraph/concepts/low_level/)
  Use for core concepts: state, nodes, edges, reducers, conditional edges, and compilation.
- [LangGraph docs: Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
  Use for checkpointers, thread IDs, graph state snapshots, and resuming interrupted runs.
- [LangChain docs: Chat models](https://python.langchain.com/docs/concepts/chat_models/)
  Use for understanding chat model invocation with system/user messages.
- [LangChain OpenAI integration](https://python.langchain.com/docs/integrations/chat/openai/)
  Use for `ChatOpenAI`, including custom OpenAI-compatible base URLs such as OpenRouter.

## Wisdom (Communities)

- [LangChain Forum](https://forum.langchain.com/)
  Use for implementation questions about LangGraph behavior and agent design tradeoffs.
- [LangChain GitHub Discussions](https://github.com/langchain-ai/langgraph/discussions)
  Use for edge cases around checkpointers, interrupts, state merging, and graph architecture.
