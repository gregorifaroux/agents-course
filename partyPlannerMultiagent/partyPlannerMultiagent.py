"""Party planner: a manager agent that delegates to a song agent and a food agent."""
from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel, tool
import requests

model = LiteLLMModel(
    model_id="ollama_chat/qwen2.5:14b",
    api_base="http://127.0.0.1:11434",
    num_ctx=16384,
    temperature=0.2,
)


@tool
def suggest_food_menu(occasion: str) -> str:
    """Suggests FOOD and drinks for a party. Returns no music.
    Args:
        occasion: One of 'casual', 'formal', or 'superhero'. Pick the closest match.
    """
    occasion = occasion.lower()
    if "casual" in occasion:
        return "{menu: 'Pizza, snacks, and drinks.'}"
    elif "formal" in occasion or "masquerade" in occasion:
        return "{menu: '3-course dinner with wine and dessert.'}"
    elif "superhero" in occasion:
        return "{menu: 'Buffet with high-energy and healthy food.'}"
    return "{menu: 'Unknown occasion. Valid options: casual, formal, superhero.'}"

@tool
def find_songs(artists: str) -> str:
    """Finds one real song per artist in the iTunes catalog.
    Call this ONCE with ALL artists in a single string.
    Args:
        artists: Artist names separated by commas. Example: 'Madonna, Iron Maiden, Ozzy Osbourne, Queen, Ice-T'
    """
    lines = []
    for name in (a.strip() for a in artists.split(",")):
        r = requests.get("https://itunes.apple.com/search", params={"term": name, "entity": "song", "limit": 5}, timeout=10)
        hits = [t for t in r.json().get("results", []) if name.lower() in t["artistName"].lower()]
        lines.append(f"{hits[0]['trackName']} - {hits[0]['artistName']}" if hits else f"No song found for {name}")
    return "\n".join(lines)

# Each worker gets only the tools it needs. The name and description are
# what the manager reads when it decides who gets which task.
song_agent = ToolCallingAgent(
    name="song_agent",
    description="Finds songs and artists for a party. Give it a party theme and a venue.",
    tools=[find_songs],
    model=model,
    max_steps=8,
    instructions=(
        "Name 5 artists whose music fits the theme, then call find_songs once per artist, "
        "for example find_songs('Billie Eilish'). Keep only songs whose artist is the one you searched. "
        "If a search returns nothing, change the keyword. "
        "Never list a song that find_songs did not return."
    ),
)

food_agent = ToolCallingAgent(
    name="food_agent",
    description="Suggests food and drinks for a party. Give it the type of party.",
    tools=[suggest_food_menu],
    model=model,
    max_steps=3,
    instructions=(
        "Only suggest food and drinks. Call the tool and print the result, "
        "then give the final answer in a later step with ONE string."
    ),
)
SONG_TASK = (
    "You are '{{name}}'. Your manager gave you this task:\n{{task}}\n\n"
    "Pick 5 artists whose music fits the task. Then call find_songs ONCE with all five names "
    "in one string, for example find_songs('Madonna, Iron Maiden, Ozzy Osbourne, Queen, Ice-T'). "
    "Your last step must be a call to the tool final_answer, with the lines find_songs returned "
    "as its answer argument. Do not write the songs as plain text. "
    "Every reply must be a tool call."
)
FOOD_TASK = (
    "You are '{{name}}'. Your manager gave you this task:\n{{task}}\n\n"
    "Call suggest_food_menu once. Then call final_answer with ONE string containing "
    "exactly the text the tool returned. Add nothing."
)
song_agent.prompt_templates["managed_agent"]["task"] = SONG_TASK
food_agent.prompt_templates["managed_agent"]["task"] = FOOD_TASK

# The manager has no tools of its own, only the two agents it can hand work to.
manager = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[song_agent, food_agent],
    max_steps=4,
    executor_kwargs={"timeout_seconds": 300},
    instructions=(
        "You are a coordinator. Do not do the workers' jobs. In ONE code block, call both workers, "
        "store each result in a variable, and print both:\n"
        "song_result = song_agent(task='...')\n"
        "food_result = food_agent(task='...')\n"
        "print(song_result)\nprint(food_result)\n"
        "In the next step, call final_answer(f'Songs:\\n{song_result}\\nMenu:\\n{food_result}') "
        "so the plan contains the workers' own text."
    ),
)

if __name__ == "__main__":
    result = manager.run(
        "Plan a villain masquerade party at Wayne's mansion. "
        "Ask song_agent for the 5 best songs and artists, and food_agent for a menu. "
        "Then combine both into one short plan."
    )
