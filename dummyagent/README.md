# dummyagent

A minimal, from-scratch ReAct-style agent that calls a local Ollama model directly via `huggingface_hub.InferenceClient`. No framework. Useful for seeing the raw Thought/Action/Observation loop.

The "tool" is a stub `get_weather(location)` that returns a nonsense value, so you can verify the loop without a real API.

## How it works

1. Send the system prompt + user question to the model, stopping generation at `Observation:`.
2. Run the tool locally and append the result as the next assistant turn's `Observation:`.
3. Call the model again to produce the `Final Answer:`.

## Run

From the project root, with Ollama reachable at `http://127.0.0.1:11434` and `qwen2:7b` pulled:

```bash
./dummyagent/dummyagent.sh
```

The script activates `.venv`, starts Ollama if it isn't running, then executes `dummyagent.py`.

## Files

- `dummyagent.py` — agent loop and stub tool.
- `dummyagent.sh` — launcher.
