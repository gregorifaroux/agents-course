from smolagents import CodeAgent, DuckDuckGoSearchTool, FinalAnswerTool, LiteLLMModel, Tool, tool, VisitWebpageTool

@tool
def suggest_menu(occasion: str) -> str:
    """
    Suggests a menu based on the occasion.
    Args:
        occasion: One of 'casual', 'formal', or 'superhero'. Pick the closest match, for example 'formal' for a formal dinner.
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
    # Example list of catering services and their ratings
    services = {
        "Gotham Catering Co.": 4.9,
        "Wayne Manor Catering": 4.8,
        "Gotham City Events": 4.7,
    }
    
    # Find the highest rated catering service (simulating search query filtering)
    best_service = max(services, key=services.get)
    
    return best_service

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


model = LiteLLMModel(
    model_id="ollama_chat/qwen2.5:14b",
    api_base="http://127.0.0.1:11434",
    num_ctx=8192,
    max_tokens=2096,
    temperature=0.5,
    custom_role_conversions=None,
    max_steps=6,

)

# Alfred, the butler, preparing the menu for the party
agent = CodeAgent(
    tools=[
        DuckDuckGoSearchTool(), 
        VisitWebpageTool(),
        suggest_menu,
        catering_service_tool,
        SuperheroPartyThemeTool(),
	FinalAnswerTool()
    ], 
    model=model,
    max_steps=10,
    verbosity_level=2
)

agent.run("Give me the best 5 songs and artist for a party at the Wayne's mansion. The party idea is a 'villain masquerade' theme")
agent.run("Suggest a menu for formal dinner")
