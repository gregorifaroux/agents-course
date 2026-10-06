"""Baseline agentic RAG: a CodeAgent with one tool (web search).

Agentic RAG = retrieval-augmented generation where the model decides when and
how to retrieve, instead of a fixed retrieve-then-generate pipeline. Here the
agent can:
  - search for party-trend terms,
  - refine the query to add "luxury",
  - synthesize the hits into a plan.

Compare with agenticRAG.py in the same folder, which swaps the web for a
BM25-indexed local knowledge base.
"""
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel


# --- Tools ------------------------------------------------------------------
search_tool = DuckDuckGoSearchTool()


# --- Model ------------------------------------------------------------------
# qwen2.5-coder:7b over qwen2:7b: the coder variant is noticeably better at
# emitting valid tool calls instead of free-text that looks like a tool call.
model = LiteLLMModel(
    model_id="ollama_chat/qwen2.5-coder:7b",
    api_base="http://127.0.0.1:11434",
    num_ctx=8192,
    max_tokens=2096,
    temperature=0.5,
    custom_role_conversions=None,
)


# --- Agent ------------------------------------------------------------------
agent = CodeAgent(
    model=model,
    tools=[search_tool],
)


# --- Run --------------------------------------------------------------------
response = agent.run(
    "Search for luxury superhero-themed party ideas, including decorations, entertainment, and catering."
)
print(response)
