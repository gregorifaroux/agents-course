# partyPlannerMultiagent

A multi-agent variant of the party-planner demo. A `CodeAgent` manager delegates to two specialist `ToolCallingAgent` workers (`song_agent`, `food_agent`) and combines their outputs into one plan.

## Topology

- **Manager** — `CodeAgent`, no tools of its own. Reads each worker's `name` + `description` and hands them tasks via `managed_agents=[...]`. The manager prompt forces a single code block that calls both workers in parallel-looking fashion, prints their results, then calls `final_answer` with the combined output.
- **song_agent** — `ToolCallingAgent` with `find_songs` only. Picks 5 artists that fit the theme, calls `find_songs` once with all names, returns the lines iTunes returned. Custom `managed_agent` task template enforces a single tool-call reply shape.
- **food_agent** — `ToolCallingAgent` with `suggest_food_menu` only. Calls the tool once and forwards its text as the final answer.

## How it differs from `partyPlanner/`

| | `partyPlanner/` | `partyPlannerMultiagent/` |
|---|---|---|
| Shape | Single agent with all tools | Manager + two specialist workers |
| Agent type | One `CodeAgent` (plus a bare `ToolCallingAgent` demo) | `CodeAgent` manager, `ToolCallingAgent` workers |
| Tool scoping | All tools visible to one agent | Each worker only sees the tools it needs |
| Song source | Agent guesses songs from web search | Dedicated worker calls the iTunes search API via `find_songs` so song/artist pairs are real |
| Coordination | Linear tool-calling loop | Manager delegates subtasks, aggregates results, then `final_answer`s |
| Prompt control | One `instructions` string on the agent | Per-worker `instructions` plus overridden `prompt_templates["managed_agent"]["task"]` |
| Telemetry | OpenInference → Langfuse | None wired up yet |

The multi-agent version is the pattern to reach for when tools fall into clearly separable responsibilities and you want the manager's reasoning kept out of the workers' tool-call traffic.

## Run

From the project root, with Ollama reachable at `http://127.0.0.1:11434` and `qwen2.5:14b` pulled:

```bash
ollama pull qwen2.5:14b
./partyPlannerMultiagent/partPlannerMultiagent.sh
```

The script activates `.venv`, starts Ollama if it isn't running, then executes `partyPlannerMultiagent.py`. The script hardcodes one manager task: plan a villain-masquerade party at Wayne's mansion, pulling songs from `song_agent` and the menu from `food_agent`.

## Files

- `partyPlannerMultiagent.py` — model, tools, two workers, manager, and the sample run.
- `partPlannerMultiagent.sh` — launcher.
