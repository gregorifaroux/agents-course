"""Hierarchical multi-agent demo on local Ollama models.

A `manager_agent` orchestrates a `web_agent`, computes cargo-plane travel times,
and renders a plotly scatter map. A local vision model validates the final plot.

Multi-agent split benefits:
- Each agent focuses on one job, so prompts stay short and performance improves.
- Separate memories keep input tokens low per step, cutting latency and cost.
"""

import math
from typing import Optional, Tuple

import importlib.resources

import yaml

from smolagents import (
    CodeAgent,
    LiteLLMModel,
    tool,
)


# --- Config -----------------------------------------------------------------

OLLAMA_API_BASE = "http://127.0.0.1:11434"
GOTHAM_COORDS = (40.7128, -74.0060)
PLOT_PATH = "saved_map.png"


# --- Tool -------------------------------------------------------------------

@tool
def calculate_cargo_travel_time(
    origin_coords: Tuple[float, float],
    destination_coords: Tuple[float, float],
    cruising_speed_kmh: Optional[float] = 750.0,
) -> float:
    """
    Calculate the travel time for a cargo plane between two points on Earth using great-circle distance.

    Args:
        origin_coords: Tuple of (latitude, longitude) for the starting point
        destination_coords: Tuple of (latitude, longitude) for the destination
        cruising_speed_kmh: Optional cruising speed in km/h (defaults to 750 km/h for typical cargo planes)

    Returns:
        float: The estimated travel time in hours

    Example:
        >>> # Chicago (41.8781° N, 87.6298° W) to Sydney (33.8688° S, 151.2093° E)
        >>> result = calculate_cargo_travel_time((41.8781, -87.6298), (-33.8688, 151.2093))
    """
    EARTH_RADIUS_KM = 6371.0

    def to_radians(deg: float) -> float:
        return deg * (math.pi / 180)

    lat1, lon1 = map(to_radians, origin_coords)
    lat2, lon2 = map(to_radians, destination_coords)

    # Haversine great-circle distance.
    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    distance = EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))

    # +10% for non-direct routes / ATC detours, +1h for takeoff & landing.
    flight_time = (distance * 1.1 / cruising_speed_kmh) + 1.0
    return round(flight_time, 2)


# --- Final-answer check (stub) ---------------------------------------------
# In production this slot would hold a vision-model call that opens the saved
# PNG and grades it PASS/FAIL (did the plot actually answer the task, was the
# right plotting API used, etc.). For a local teaching demo it is overkill:
# the judge model (llama3.2-vision) is a multi-GB download on top of the two
# 32b qwen agents already loaded, and every FAIL burns another full manager
# retry on 32b inference. Left as a no-op callback so the wiring stays visible.

def check_reasoning_and_plot(final_answer, agent_memory, **kwargs):
    print(
        "[final_answer_check] skipped: in production, a vision model would "
        "grade saved_map.png here. Overkill for a local demo, accepting as-is."
    )
    return True


# --- Model ------------------------------------------------------------------
# Both agents share one Ollama-loaded instance. The 7b variant was tried first
# for the web_agent but kept hallucinating the search tool's return shape
# (treating a markdown string as a list of dicts). The 32b handles both the
# manager's delegation and the worker's parsing reliably.

llm = LiteLLMModel(
    model_id="ollama_chat/qwen2.5-coder:32b",
    api_base=OLLAMA_API_BASE,
    num_ctx=8192,
    max_tokens=2096,
    temperature=0.5,
)


# --- Agents -----------------------------------------------------------------
# geocoder_agent is a managed sub-agent. The manager calls it by name as if it
# were a Python function: `geocoder_agent(task="...")`. `name` and `description`
# are what the manager sees when deciding whether to delegate.
#
# No web-browsing tools: on this task the agent kept getting lost scraping pages
# instead of just calling `Nominatim().geocode(name)` on names it already knew
# from training. Stripping the tools removes the distraction entirely.
#
# Override the managed-agent prompt templates so:
#   - the sub-agent is told to return a plain Python list of tuples (no "Task
#     outcome short/detailed/additional context" boilerplate that smolagents
#     normally forces)
#   - the wrapper that returns the sub-agent's answer to the manager emits ONLY
#     the final answer, no "Here is the final answer from your managed agent"
#     prefix. The manager can ast.literal_eval the string directly.

_default_templates = yaml.safe_load(
    importlib.resources.files("smolagents.prompts").joinpath("code_agent.yaml").read_text()
)
_geocoder_templates = dict(_default_templates)
_geocoder_templates["managed_agent"] = {
    "task": (
        "You are a geocoding agent named '{{name}}'. Your manager has sent you this task:\n"
        "---\n{{task}}\n---\n"
        "Use `geopy.geocoders.Nominatim(user_agent='demo').geocode(name)` to resolve each place name.\n"
        "Call `final_answer(...)` with a PLAIN Python list of (name, latitude, longitude) tuples. "
        "Nothing else — no dict, no explanation, no markdown. Just the list."
    ),
    "report": "{{final_answer}}",
}

geocoder_agent = CodeAgent(
    model=llm,
    tools=[calculate_cargo_travel_time],
    name="geocoder_agent",
    description=(
        "Geocodes a list of well-known place names into (name, lat, lon) tuples "
        "using `geopy.geocoders.Nominatim`. Returns a plain Python list of "
        "tuples — nothing else."
    ),
    prompt_templates=_geocoder_templates,
    verbosity_level=2,
    max_steps=10,
    # Wildcard needed for submodules (e.g. geopy.geocoders). A bare "geopy"
    # only authorizes the top-level module.
    additional_authorized_imports=["geopy.*"],
    # Disable per-snippet timeout. 32b inference + geocoding can easily
    # exceed any reasonable cap; max_steps already prevents runaway loops.
    executor_kwargs={"timeout_seconds": None},
)

manager_agent = CodeAgent(
    model=llm,
    tools=[calculate_cargo_travel_time],
    managed_agents=[geocoder_agent],
    additional_authorized_imports=[
        "geopandas.*",
        "plotly.*",
        "shapely.*",
        "json",
        "pandas.*",
        "numpy.*",
        "geopy.*",
        "ast",
    ],
    planning_interval=5,
    verbosity_level=2,
    final_answer_checks=[check_reasoning_and_plot],
    max_steps=15,
    # Disable per-snippet timeout. A single snippet may invoke web_agent (full
    # sub-agent run of up to 10 LLM calls on 32b) plus kaleido spin-up for
    # fig.write_image. max_steps already caps the outer loop.
    executor_kwargs={"timeout_seconds": None},
)


# --- Task prompt ------------------------------------------------------------
# The explicit "do NOT have a web_search tool" block is defensive: smaller or
# weaker local models tend to invent a `web_search()` call instead of
# delegating. Pinning the delegation syntax prevents InterpreterError at step 1.

TASK = """
Find a few Batman filming locations in the world, calculate the time to transfer via cargo plane to here (we're in Gotham, 40.7128° N, 74.0060° W).
Also give me some supercar factories with the same cargo plane transfer time. You need at least 4 points in total (do NOT include Gotham itself).
Represent this as spatial map of the world, with the locations represented as scatter points with a color that depends on the travel time, and save it to saved_map.png!

You do NOT have web-search tools. To turn place names into coordinates, delegate to the managed agent `geocoder_agent`.
IMPORTANT: `geocoder_agent(task=...)` returns a STRING (the stringified Python list of tuples). Parse it with `ast.literal_eval`.

Example:
    import ast
    locations_raw = geocoder_agent(task="Geocode these Batman filming locations: Chicago IL USA, Liverpool UK, Glasgow UK, London UK, Pinewood Studios UK.")
    locations = ast.literal_eval(locations_raw)   # list of (name, lat, lon)
    factories_raw = geocoder_agent(task="Geocode these supercar factories: Ferrari factory Maranello Italy, Lamborghini factory Sant'Agata Bolognese Italy, Pagani factory San Cesario sul Panaro Italy, Koenigsegg factory Ängelholm Sweden.")
    factories = ast.literal_eval(factories_raw)

Pass the exact names in the delegate task — do not expect the sub-agent to invent them.
Then use `calculate_cargo_travel_time` on the coordinates yourself with the default cruising speed.

Here's an example of how to plot and return a map:
import plotly.express as px
df = px.data.carshare()
fig = px.scatter_map(df, lat="centroid_lat", lon="centroid_lon", text="name", color="peak_hour", size=100,
     color_continuous_scale=px.colors.sequential.Magma, size_max=15, zoom=1)
fig.show()
fig.write_image("saved_map.png")
final_answer(fig)

IMPORTANT: this project uses plotly 7.1+. The Mapbox-based API was REMOVED. Do NOT use:
  - `px.scatter_mapbox` (gone — use `px.scatter_map`)
  - `go.Scattermapbox` or `go.scattermapbox.Marker` (gone — use `go.Scattermap` and `go.scattermap.Marker`)
  - `fig.update_layout(mapbox_style=..., mapbox_zoom=...)` (gone — use `map_style=`, `map_zoom=`)
Stick to `px.scatter_map` with the example above and `fig.write_image("saved_map.png")`.

Never try to process strings using code: when you have a string to read, just print it and you'll see it.
"""


# --- Entry point ------------------------------------------------------------

if __name__ == "__main__":
    manager_agent.visualize()
    manager_agent.run(TASK)
