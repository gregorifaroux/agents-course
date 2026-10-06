"""Single-agent party planner with Langfuse tracing.

A CodeAgent (Alfred the butler) is given a mix of tools: live web search,
page fetch, a food-menu lookup, a catering picker, and a theme generator.
The same prompt is also run through a ToolCallingAgent at the bottom to show
the two execution styles smolagents supports.

Tracing: OpenInference's SmolagentsInstrumentor hooks every agent step and
ships it to Langfuse. Credentials come from a .env file via python-dotenv.
"""
from dotenv import load_dotenv
from smolagents import (
    CodeAgent,
    DuckDuckGoSearchTool,
    FinalAnswerTool,
    LiteLLMModel,
    Tool,
    ToolCallingAgent,
    VisitWebpageTool,
    tool,
)

# --- Tracing ----------------------------------------------------------------
# load_dotenv must run before get_client() so the Langfuse env vars are set.
load_dotenv()

from langfuse import get_client

langfuse = get_client()

if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")

# Attach the smolagents instrumentor. From this point on every agent run
# emits spans that Langfuse picks up automatically.
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

SmolagentsInstrumentor().instrument()


# --- Tools ------------------------------------------------------------------

@tool
def suggest_food_menu(occasion: str) -> str:
    """
    Suggests FOOD and drinks for a party. It does not return music or songs.
    Args:
        occasion: One of 'casual', 'formal', or 'superhero'. Pick the closest match.
    """
    occasion = occasion.lower()
    if "casual" in occasion:
        return "Pizza, snacks, and drinks."
    elif "formal" in occasion:
        return "3-course dinner with wine and dessert."
    elif "superhero" in occasion:
        return "Buffet with high-energy and healthy food."
    else:
        return "Unknown occasion. Valid options: casual, formal, superhero."

@tool
def catering_service_tool(query: str) -> str:
    """
    This tool returns the highest-rated catering service in Gotham City.

    Args:
        query: A search term for finding catering services.
    """
    # Stand-in catalog: in a real app this would come from a vendor API.
    services = {
        "Gotham Catering Co.": 4.9,
        "Wayne Manor Catering": 4.8,
        "Gotham City Events": 4.7,
    }

    # `query` is accepted but ignored for this toy version. The point is to
    # show the agent calling a tool with a free-text argument.
    best_service = max(services, key=services.get)

    return best_service


# A full Tool subclass (not an @tool decorator) because real tools often
# need state, config, or custom __init__ logic. The agent sees them the same.
class SuperheroPartyThemeTool(Tool):
    name = "superhero_party_theme_generator"
    description = """
    This tool suggests creative superhero-themed party ideas based on a category.
    It returns a unique party theme idea."""
    
    inputs = {
        "category": {
            "type": "string",
            "description": "The type of superhero party (e.g., 'classic heroes', 'villain masquerade', 'futuristic Gotham').",
        }
    }
    
    output_type = "string"

    def forward(self, category: str):
        themes = {
            "classic heroes": "Justice League Gala: Guests come dressed as their favorite DC heroes with themed cocktails like 'The Kryptonite Punch'.",
            "villain masquerade": "Gotham Rogues' Ball: A mysterious masquerade where guests dress as classic Batman villains.",
            "futuristic gotham": "Neo-Gotham Night: A cyberpunk-style party inspired by Batman Beyond, with neon decorations and futuristic gadgets."
        }
        
        return themes.get(category.lower(), "Themed party idea not found. Try 'classic heroes', 'villain masquerade', or 'futuristic Gotham'.")


# --- Model ------------------------------------------------------------------
# qwen2.5:14b: the 7b variants struggled to keep the multi-tool plan
# coherent for this many tools. The 14b handles the orchestration cleanly.

model = LiteLLMModel(
    model_id="ollama_chat/qwen2.5:14b",
    api_base="http://127.0.0.1:11434",
    num_ctx=8192,
    max_tokens=2096,
    temperature=0.5,
    custom_role_conversions=None,
    max_steps=6,
)


# --- CodeAgent --------------------------------------------------------------
# Alfred, the butler. CodeAgent means the LLM emits Python snippets that the
# sandbox runs; snippets can call any tool in `tools` as a normal function.

agent = CodeAgent(
    tools=[
        DuckDuckGoSearchTool(),
        VisitWebpageTool(),
        suggest_food_menu,
        catering_service_tool,
        SuperheroPartyThemeTool(),
        FinalAnswerTool()
    ],
    model=model,
    # The one-tool-per-block rule guards against a common failure where the
    # model calls `final_answer(something(...))` and loses the intermediate
    # result from the trace.
    instructions="Call one tool at a time and print the result. Never call final_answer in the same code block as another tool.",
    max_steps=10,
    verbosity_level=2
)

agent.run("Use the web search tool to find best 5 songs and artist for a party at the Wayne's mansion. The party idea is a 'villain masquerade' theme")
agent.run("Suggest a menu for formal dinner")


# --- ToolCallingAgent -------------------------------------------------------
# Second execution style: instead of generating Python, the model emits JSON
# tool-call payloads (the OpenAI/Anthropic native format). smolagents parses
# them and runs the tools. Lower expressive power than CodeAgent but easier
# for weaker models to get right.

agentJSON = ToolCallingAgent(tools=[DuckDuckGoSearchTool()], model=model)
agentJSON.run("Search for the best music recommendations for a party at the Wayne's mansion.")