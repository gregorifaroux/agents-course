# partyPlannerMultiagentUI

The same manager/worker party-planner as [`partyPlannerMultiagent/`](../partyPlannerMultiagent/README.md), wrapped in `smolagents.GradioUI` so you can submit the party brief from a browser chat window instead of hardcoding it in the script.

## How it differs from `partyPlannerMultiagent/`

- The script does not call `manager.run(...)`. It calls `GradioUI(manager).launch(share=False)`, using the built-in UI from `smolagents` that renders intermediate thoughts (planning steps, tool calls, execution logs) as collapsible blocks.
- The user types each party brief in the chat UI; the manager still delegates to `song_agent` and `food_agent` under the hood.
- The manager carries a `name` and `description` so the Gradio header shows the agent identity. smolagents requires `name` to be a valid Python identifier, so the display name lives in `description`:
  - `name="devoted_butler"`
  - `description="Devoted Butler. Help plan your party... music, food, you name it."`
- Everything else (model, tools, worker definitions, prompt templates, manager instructions) is unchanged.

## Run

From the project root, with Ollama reachable at `http://127.0.0.1:11434` and `qwen2.5:14b` pulled:

```bash
ollama pull qwen2.5:14b
./partyPlannerMultiagentUI/partyPlannerMultiagentUI.sh
```

Gradio prints a local URL. Open it, type a party brief (for example "Plan a villain masquerade party at Wayne's mansion"), and the manager will coordinate the two workers and return the combined plan.

## Files

- `partyPlannerMultiagentUI.py` — model, tools, workers, manager, Gradio launch.
- `partyPlannerMultiagentUI.sh` — launcher.
