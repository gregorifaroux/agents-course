# agents-course

A smolagents `CodeAgent` wired to a local Ollama model (`qwen2:7b` via LiteLLM) and exposed through a Gradio UI.

## Tools

- `roll_dice` — roll N dice with S sides.
- `get_current_time_in_timezone` — current time for an IANA timezone.
- `get_weather` — current weather from `wttr.in`.
- `DuckDuckGoSearchTool` — web search.
- `FinalAnswerTool` — required terminator for the agent loop.
- `agents-course/text-to-image` — loaded from the Hub.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) installed (`brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [Ollama](https://ollama.com/) running locally with the `qwen2:7b` model pulled:

```bash
ollama pull qwen2:7b
```

## Setup

Create a virtual environment and install dependencies with uv:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Run

With the venv active and Ollama reachable at `http://127.0.0.1:11434`:

```bash
python app.py
```

Or use the helper script, which activates the venv and starts Ollama if it isn't already running:

```bash
./app.sh
```

Gradio will print a local URL. Open it to chat with the agent.

## Files

- `app.py` — agent definition, tools, and Gradio launch.
- `prompts.yaml` — system prompt templates passed to `CodeAgent`.
- `tools/final_answer.py` — final-answer tool.
- `Gradio_UI.py` — UI wrapper.
- `requirements.txt` — Python dependencies.
- `app.sh` — convenience launcher.

## Subfolders

- `dummyagent/` — minimal from-scratch ReAct agent calling Ollama directly via `huggingface_hub`. See [`dummyagent/README.md`](dummyagent/README.md).
- `testlocalmodel/` — smoke test for the Ollama + LiteLLM wiring. See [`testlocalmodel/README.md`](testlocalmodel/README.md).
