"""smolagents Tool that wraps DuckDuckGo and returns results as markdown."""
from typing import Any, Optional

import duckduckgo_search
from smolagents.tools import Tool


class DuckDuckGoSearchTool(Tool):
    """Run a DuckDuckGo text search and return the top N hits as markdown.

    The output is a single string with `[title](url)\\nsnippet` blocks. An agent
    that wants to visit a page has to parse the url out of that string, since
    the tool returns markdown rather than structured JSON.
    """

    name = "web_search"
    description = "Performs a duckduckgo web search based on your query (think a Google search) then returns the top search results."
    inputs = {'query': {'type': 'string', 'description': 'The search query to perform.'}}
    output_type = "string"

    def __init__(self, max_results=10, **kwargs):
        super().__init__()
        self.max_results = max_results
        # Import lazily so the tool module can be loaded even on a machine
        # that has not installed duckduckgo-search yet.
        try:
            from duckduckgo_search import DDGS
        except ImportError as e:
            raise ImportError(
                "You must install package `duckduckgo_search` to run this tool: for instance run `pip install duckduckgo-search`."
            ) from e
        self.ddgs = DDGS(**kwargs)

    def forward(self, query: str) -> str:
        results = self.ddgs.text(query, max_results=self.max_results)
        # Raising (vs. returning "no results") pushes the agent to retry with a
        # different query instead of hallucinating an answer from nothing.
        if len(results) == 0:
            raise Exception("No results found! Try a less restrictive/shorter query.")
        postprocessed_results = [f"[{result['title']}]({result['href']})\n{result['body']}" for result in results]
        return "## Search Results\n\n" + "\n\n".join(postprocessed_results)
