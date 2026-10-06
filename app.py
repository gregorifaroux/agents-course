"""Entry point for the course's starter agent.

A single CodeAgent runs on a local Ollama model and exposes four tools (dice,
time, weather, web search) plus `final_answer`. The agent is wrapped in a
Gradio UI so the user can chat with it in the browser.
"""

import datetime
import random

import pytz
import requests
import yaml
from smolagents import CodeAgent, DuckDuckGoSearchTool, GradioUI, LiteLLMModel, tool

from tools.final_answer import FinalAnswerTool


# --- Tools ------------------------------------------------------------------
# Each `@tool` function below is exposed to the agent. The docstring is what
# the model reads to decide when to call the tool, so it has to describe both
# the purpose and every argument.

@tool
def roll_dice(sides: int = 20, count: int = 1) -> str:
    """Roll one or more dice and return the individual rolls and their total.
    Use this for any request to roll dice, flip a random number, or resolve a game action by chance.
    Args:
        sides: Number of sides on each die, for example 6 or 20.
        count: How many dice to roll.
    """
    # Guard against pathological inputs (0-sided dice, 10k-roll requests) that
    # would waste tokens on an unusable result.
    if sides < 2 or not 1 <= count <= 100:
        return "Invalid input: sides must be 2 or more, count between 1 and 100."
    rolls = [random.randint(1, sides) for _ in range(count)]
    return f"Rolled {count}d{sides}: {rolls}, total {sum(rolls)}"


@tool
def get_current_time_in_timezone(timezone: str = "America/Chicago") -> str:
    """A tool that fetches the current local time in a specified timezone.
    Args:
        timezone: A string representing a valid timezone (e.g., 'America/New_York').
    """
    try:
        tz = pytz.timezone(timezone)
        local_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"The current local time in {timezone} is: {local_time}"
    except Exception as e:
        # Return the error as a string so the agent can read it and retry
        # with a valid timezone, rather than crashing the loop.
        return f"Error fetching time for timezone '{timezone}': {str(e)}"


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.
    Args:
        city: Name of the city, for example 'Paris'.
    """
    # wttr.in returns a one-line summary when format=3, which keeps the
    # observation short in the agent's context window.
    r = requests.get(f"https://wttr.in/{city}", params={"format": "3"}, timeout=10)
    return r.text


# --- Model ------------------------------------------------------------------
# LiteLLMModel is a thin wrapper that lets smolagents talk to any provider
# supported by LiteLLM. Here we point it at a local Ollama server.

final_answer = FinalAnswerTool()
model = LiteLLMModel(
    model_id="ollama_chat/qwen2:7b",
    api_base="http://127.0.0.1:11434",
    num_ctx=8192,
    max_tokens=2096,
    temperature=0.5,
    custom_role_conversions=None,
)


# --- Agent ------------------------------------------------------------------
# The system prompt and ReAct scaffolding live in prompts.yaml so they can be
# tweaked without touching code.

with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)

agent = CodeAgent(
    model=model,
    # final_answer must stay in the tool list: it is how the agent terminates.
    tools=[final_answer, DuckDuckGoSearchTool(), roll_dice, get_current_time_in_timezone, get_weather],
    max_steps=6,
    verbosity_level=1,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates,
)


# --- Entry point ------------------------------------------------------------
# share=False keeps the Gradio tunnel disabled; the UI only binds to localhost.

GradioUI(agent).launch(share=False)