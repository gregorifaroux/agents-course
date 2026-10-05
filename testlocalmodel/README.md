# testlocalmodel

Smoke test for the Ollama + LiteLLM wiring used by the main agent. Sends two one-shot prompts through `smolagents.LiteLLMModel` pointed at local `qwen2:7b` and prints the responses.

Not a unit test suite. Use it to confirm the model is reachable and responding before touching `app.py`.

## Run

From the project root, with Ollama reachable at `http://127.0.0.1:11434` and `qwen2:7b` pulled:

```bash
./testlocalmodel/testlocalmodel.sh
```

The script activates `.venv`, starts Ollama if it isn't running, then executes `testlocalmodel.py`.

## Files

- `testlocalmodel.py` — two sample prompts against `LiteLLMModel`.
- `testlocalmodel.sh` — launcher.
