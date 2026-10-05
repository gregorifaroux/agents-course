
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel, GradioUI, load_tool, tool
import datetime
import pytz
import requests
import yaml
import random
from tools.final_answer import FinalAnswerTool

# a tool that rolls dice e.g. roll 2d6, roll a d20 for initiative
@tool
def roll_dice(sides: int = 20, count: int = 1) -> str:
    """Roll one or more dice and return the individual rolls and their total.
    Use this for any request to roll dice, flip a random number, or resolve a game action by chance.
    Args:
        sides: Number of sides on each die, for example 6 or 20.
        count: How many dice to roll.
    """
    if sides < 2 or not 1 <= count <= 100:
        return "Invalid input: sides must be 2 or more, count between 1 and 100."
    rolls = [random.randint(1, sides) for _ in range(count)]
    return f"Rolled {count}d{sides}: {rolls}, total {sum(rolls)}"
    return "What magic will you build ?"

@tool
def get_current_time_in_timezone(timezone: str = "America/Chicago") -> str:
    """A tool that fetches the current local time in a specified timezone.
    Args:
        timezone: A string representing a valid timezone (e.g., 'America/New_York').
    """
    try:
        # Create timezone object
        tz = pytz.timezone(timezone)
        # Get current time in that timezone
        local_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"The current local time in {timezone} is: {local_time}"
    except Exception as e:
        return f"Error fetching time for timezone '{timezone}': {str(e)}"

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.
    Args:
        city: Name of the city, for example 'Paris'.
    """
    r = requests.get(f"https://wttr.in/{city}", params={"format": "3"}, timeout=10)
    return r.text

final_answer = FinalAnswerTool()
model = LiteLLMModel(
    model_id="ollama_chat/qwen2:7b",
    api_base="http://127.0.0.1:11434",
    num_ctx=8192,
    max_tokens=2096,
    temperature=0.5,
    custom_role_conversions=None,
) 

# Import tool from Hub
image_generation_tool = load_tool("agents-course/text-to-image", trust_remote_code=True)

# Load system prompt from prompt.yaml file
with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)
    
agent = CodeAgent(
    model=model,
    tools=[final_answer, DuckDuckGoSearchTool(), roll_dice, get_current_time_in_timezone, get_weather], # add your tools here (don't remove final_answer)
    max_steps=6,
    verbosity_level=1,
    #grammar=None,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates # Pass system prompt to CodeAgent
)


GradioUI(agent).launch(share=False)