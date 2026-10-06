# AgenticRAG

Two smolagents examples backed by a local Ollama model.

- `basicRAG.py`: `CodeAgent` with `DuckDuckGoSearchTool` for web-search-backed RAG.
- `agenticRAG.py`: `CodeAgent` with a BM25 retriever over an in-memory party-ideas corpus.

Both scripts call Ollama at `http://127.0.0.1:11434` via LiteLLM.

## Prerequisites

- Python venv at `../.venv` (activated by the `.sh` launchers).
- [Ollama](https://ollama.com) installed and on PATH.

## Python dependencies

`agenticRAG.py` needs LangChain packages beyond the base `requirements.txt`. From the repo root with the venv active:

```bash
uv pip install langchain-community langchain-text-splitters rank-bm25
```

`rank-bm25` is required at `BM25Retriever` construction time; without it you get a runtime error, not an import error.

## Pull the model

Both scripts use `qwen2.5-coder:7b`. Pull it once:

```bash
ollama pull qwen2.5-coder:7b
```

Verify:

```bash
ollama list | grep qwen2.5-coder
```

Why this model: qwen2:7b hallucinates tool calls (e.g. invents `visit_webpage`) under `CodeAgent`. qwen2.5-coder:7b follows the tool list more reliably and emits cleaner Python code blocks.

If you want to try a different one, change `model_id` in `basicRAG.py` / `agenticRAG.py`. Candidates: `qwen2.5-coder:14b`, `llama3.1:8b`.

## Run

The `.sh` launchers start Ollama if it isn't running, then invoke Python:

```bash
./basicRAG.sh    # runs basicRAG.py
./agenticRAG.sh  # runs agenticRAG.py
```

Or directly, assuming Ollama is up and the venv is active:

```bash
python basicRAG.py
python agenticRAG.py
```

## Troubleshooting

- `InterpreterError: Forbidden function evaluation: 'visit_webpage' is not among the explicitly allowed tools`
  The model invented a tool that wasn't registered. Either add it (`from smolagents import VisitWebpageTool`) to the agent's `tools=[...]`, or switch to a stronger model.

- Ollama connection refused: confirm `ollama serve` is running and `curl http://127.0.0.1:11434` returns `Ollama is running`.
