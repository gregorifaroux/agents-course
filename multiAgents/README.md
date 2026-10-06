# multiAgents

Hierarchical multi-agent demo built on `smolagents`. A **manager** agent orchestrates a **geocoder_agent** sub-agent, plans a plot, and emits a scatter map on top of OpenStreetMap tiles.

## Task

Find Batman filming locations + supercar factories worldwide, compute cargo-plane travel time from each to Gotham (40.7128° N, 74.0060° W), and render them as a `plotly.express.scatter_map`, saved to `saved_map.png`.

## Why multi-agent

Two reasons:

1. **Focus.** Each agent has one job and a small tool belt. Short, specialized prompts beat a single mega-prompt that must handle search, math, and plotting at once.
2. **Memory isolation.** The manager never sees the raw geocoder requests or intermediate retries the `geocoder_agent` chewed through. It only receives the sub-agent's final answer. Smaller per-step context means lower latency, lower cost, and less chance of the model drowning in noise.

## Agents

**`geocoder_agent`** (worker, `qwen2.5-coder:32b`)
- Role: turn well-known place names into `(name, lat, lon)` tuples via `geopy.geocoders.Nominatim`.
- Tools: `calculate_cargo_travel_time`. Authorized imports: `geopy.*`. No web-search tools.
- Called by the manager as `geocoder_agent(task="Geocode: name1, name2, …")`.
- `verbosity_level=2` (traces to stdout), `max_steps=10`.
- Started as a `web_agent` with `DuckDuckGoSearchTool` + `VisitWebpageTool`. The model kept getting lost scraping article pages instead of just geocoding names it already knew. Stripping the browsing tools removed the distraction. On 7b first; swapped to 32b after it hallucinated the search tool's return shape (treated a markdown string as a list of dicts).

**`manager_agent`** (orchestrator, `qwen2.5-coder:32b`)
- Role: plan the task, delegate name-to-coordinate work to `geocoder_agent`, compute flight times, build the plotly map, save PNG, call `final_answer`.
- Tools: `calculate_cargo_travel_time` (direct) + `geocoder_agent` (managed sub-agent).
- Authorized imports: `geopandas`, `plotly`, `shapely`, `json`, `pandas`, `numpy`.
- `planning_interval=5` (re-plans every 5 steps), `verbosity_level=2` (full trace to stdout), `max_steps=15`.
- `final_answer_checks=[check_reasoning_and_plot]` must pass before the loop terminates.

**Vision validator** (callback, not an agent — `llama3.2-vision:11b`)
- Role: look at the saved PNG, grade PASS/FAIL on whether the plot answers the task.
- Wired as a `final_answer_checks` callback. No tools, no planning loop — just one LLM call that raises on FAIL so the manager retries.

## Flow

```
TASK
  └─ manager_agent plans
        ├─ geocoder_agent(task="Geocode: Chicago, Liverpool, Glasgow, …")  → list of (name, lat, lon)
        ├─ geocoder_agent(task="Geocode: Ferrari Maranello, Lamborghini Sant'Agata, …")  → list of (name, lat, lon)
        ├─ calculate_cargo_travel_time(...) per point
        ├─ build plotly scatter_map, fig.write_image("saved_map.png")
        └─ final_answer(fig)
              └─ check_reasoning_and_plot (vision model grades the PNG)
                    PASS → done
                    FAIL → raises, manager retries
```

The manager has no search or page-visit tools. It delegates to `geocoder_agent(task="...")` as a function. The task prompt passes the exact place names to the delegate so the sub-agent doesn't have to invent them.

## Model choice

Both agents share one `qwen2.5-coder:32b` instance via Ollama. Ollama keeps a single copy of the weights loaded, so running two agents against it costs the same memory as one.

Attempted the 7b for the sub-agent first (fast and cheap). When it still had `DuckDuckGoSearchTool`, it couldn't parse the markdown-string output — repeatedly wrote `result['url']` as if the return were a list of dicts. The 32b handles the format correctly. Later the browsing tools came off entirely, so this specific failure mode is now irrelevant to the current flow.

Fully local. No API keys needed for the agent loop itself.

## Requirements

Python deps (installed from parent `requirements.txt`):

```
smolagents[litellm]  plotly  geopandas  shapely  kaleido
duckduckgo_search  ddgs  pandas  pillow
```

Install from repo root:

```bash
uv pip install -r requirements.txt
```

## Ollama models

```bash
ollama pull qwen2.5-coder:32b        # manager + geocoder_agent
ollama pull llama3.2-vision:11b      # final-answer vision check
ollama serve                         # must be running on 127.0.0.1:11434
```

The 32b model is ~20 GB. Needs enough unified memory / VRAM to load it; on Apple Silicon, ≥32 GB RAM is comfortable.

## Final-answer vision check

`check_reasoning_and_plot` passes the saved PNG to a local vision model (`llama3.2-vision:11b` via Ollama) to validate the plot. Fully local — no API keys needed.

To disable the check entirely, remove `final_answer_checks=[check_reasoning_and_plot]` from `manager_agent`.

## Run

```bash
cd multiAgents
python multiAgents.py
```

Output artifacts:

- `saved_map.png` — the scatter map.
- Agent trace printed to stdout (`verbosity_level=2` on the manager).

## Gotchas

- **"web_search is not among the explicitly allowed tools"** — the manager tried to call a nonexistent tool. The current prompt pins it to `geocoder_agent(task="...")`; keep that section if you edit the task.
- **`kaleido`** is required by `fig.write_image("saved_map.png")`. Already in `requirements.txt`.
- **Context window** — `num_ctx=8192`. Raise it if the manager truncates mid-plan.
- **Temperature** — set to `0.5`; drop to `0.2` for more deterministic runs.
- **"Code execution exceeded the maximum execution time of 30 seconds" / `TimeoutError`** — smolagents' default per-snippet timeout. One manager snippet can trigger a full `geocoder_agent(...)` run (up to 10 LLM calls on 32b) plus `fig.write_image` (kaleido spins up a Chromium). Disabled via `executor_kwargs={"timeout_seconds": None}` on both agents; `max_steps` already caps the loop.
- **Agent scraping pages instead of geocoding** — resolved by dropping `DuckDuckGoSearchTool` and `VisitWebpageTool` from the sub-agent. Without browsing tools, it goes straight to `Nominatim`.
- **"Import from geopy.geocoders is not allowed"** — smolagents' authorization is tree-based without implicit submodule access. Use `"geopy.*"` (wildcard), not bare `"geopy"`, in `additional_authorized_imports`.

## Files

- `multiAgents.py` — agents, tool, task, and vision check callback.
- `saved_map.png` — generated at runtime.
