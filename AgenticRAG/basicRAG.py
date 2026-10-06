# Agentic RAG (Retrieval-Augmented Generation) extends traditional RAG systems by combining autonomous agents with dynamic knowledge retrieval.

# Let’s build a simple agent that can search the web using DuckDuckGo. This agent will retrieve information and synthesize responses to answer queries. With Agentic RAG, Alfred’s agent can:

# Search for latest superhero party trends
# Refine results to include luxury elements
# Synthesize information into a complete plan

from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel

# Initialize the search tool
search_tool = DuckDuckGoSearchTool()

# Initialize the model
model = LiteLLMModel(
    model_id="ollama_chat/qwen2.5-coder:7b",
    api_base="http://127.0.0.1:11434",
    num_ctx=8192,
    max_tokens=2096,
    temperature=0.5,
    custom_role_conversions=None,
)

agent = CodeAgent(
    model=model,
    tools=[search_tool],
)

# Example usage
response = agent.run(
    "Search for luxury superhero-themed party ideas, including decorations, entertainment, and catering."
)
print(response)
