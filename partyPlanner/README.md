# partyPlanner

A smolagents `CodeAgent` roleplaying Alfred planning a party at Wayne Manor. Uses a local Ollama model (`qwen2.5:14b` via LiteLLM) and a mix of custom tools plus web search.

## Tools

- `suggest_menu(occasion)` — returns a menu for `casual`, `formal`, or `superhero`.
- `catering_service_tool(query)` — returns the top-rated Gotham caterer from a hardcoded list.
- `SuperheroPartyThemeTool` — class-based tool returning a themed party idea for `classic heroes`, `villain masquerade`, or `futuristic gotham`.
- `DuckDuckGoSearchTool` — web search.
- `VisitWebpageTool` — fetch a webpage.
- `FinalAnswerTool` — required terminator for the agent loop.

## Run

From the project root, with Ollama reachable at `http://127.0.0.1:11434` and `qwen2.5:14b` pulled:

```bash
ollama pull qwen2.5:14b
./partyPlanner/partyPlanner.sh
```

The script activates `.venv`, starts Ollama if it isn't running, then executes `partyPlannerAgent.py`. The script hardcodes two prompts: one asking for party songs with a villain-masquerade theme, one asking for a formal dinner menu.

## Files

- `partyPlannerAgent.py` — tool definitions, model config, agent, and sample prompts.
- `partyPlanner.sh` — launcher.
