# partyPlanner

A smolagents agent roleplaying Alfred planning a party at Wayne Manor. Uses a local Ollama model (`qwen2.5:14b` via LiteLLM) and a mix of custom tools plus web search. Instrumented with OpenInference and traces exported to Langfuse.

Runs two agent variants back-to-back from the same script: a `CodeAgent` (primary) and a `ToolCallingAgent` (for comparison).

## CodeAgent vs ToolCallingAgent

Both are smolagents agent types; they differ in how the model expresses a tool call.

- `CodeAgent` — the model emits a Python snippet per step. smolagents executes it, so one block can call multiple tools, pass results between them, and do arithmetic or control flow. More expressive, but the model has to write valid Python and respect sequencing (the script passes `instructions="Call one tool at a time ... never call final_answer in the same code block as another tool."` to keep steps clean).
- `ToolCallingAgent` — the model emits a JSON tool call per step via the provider's native tool-calling interface (the format OpenAI, Anthropic, and others expose). One tool per step, structured arguments, no code execution. Simpler and safer; less expressive for multi-step composition in a single turn.

The script uses `CodeAgent` for the full tool suite and spins up a bare `ToolCallingAgent` with only `DuckDuckGoSearchTool` to show the JSON-call style on the same model.

## Tools (CodeAgent)

- `suggest_food_menu(occasion)` — returns a food/drink menu for `casual`, `formal`, or `superhero`. Explicitly not a music tool.
- `catering_service_tool(query)` — returns the top-rated Gotham caterer from a hardcoded list.
- `SuperheroPartyThemeTool` — class-based tool returning a themed party idea for `classic heroes`, `villain masquerade`, or `futuristic gotham`.
- `DuckDuckGoSearchTool` — web search.
- `VisitWebpageTool` — fetch a webpage.
- `FinalAnswerTool` — required terminator for the agent loop.

## Telemetry

The agent is instrumented via `openinference-instrumentation-smolagents` and ships traces to Langfuse. Credentials are read from a `.env` at the project root:

```
LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_BASE_URL=...
```

On startup the agent calls `langfuse.auth_check()` and prints whether the client authenticated. Traces appear in the configured Langfuse project.

## Run

From the project root, with Ollama reachable at `http://127.0.0.1:11434` and `qwen2.5:14b` pulled:

```bash
ollama pull qwen2.5:14b
./partyPlanner/partyPlanner.sh
```

The script activates `.venv`, starts Ollama if it isn't running, then executes `partyPlannerAgent.py`. The script hardcodes three prompts: `CodeAgent` runs one asking for party songs with a villain-masquerade theme and one asking for a formal dinner menu; `ToolCallingAgent` then runs a music-recommendation search.

## Files

- `partyPlannerAgent.py` — tool definitions, model config, agent, and sample prompts.
- `partyPlanner.sh` — launcher.
