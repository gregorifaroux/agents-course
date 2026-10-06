"""smolagents Tool that fetches a URL and returns a truncated markdown rendering."""
import re
from typing import Any, Optional

import requests
import markdownify
import smolagents
from smolagents.tools import Tool


class VisitWebpageTool(Tool):
    """Fetch an HTTP(S) URL and return its content as markdown, capped at 10k chars."""

    name = "visit_webpage"
    description = "Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages."
    inputs = {'url': {'type': 'string', 'description': 'The url of the webpage to visit.'}}
    output_type = "string"

    def forward(self, url: str) -> str:
        # Re-import inside forward so the tool can be shipped as a self-contained
        # snippet to a sandboxed executor that only has smolagents loaded.
        try:
            import requests
            from markdownify import markdownify
            from requests.exceptions import RequestException

            from smolagents.utils import truncate_content
        except ImportError as e:
            raise ImportError(
                "You must install packages `markdownify` and `requests` to run this tool: for instance run `pip install markdownify requests`."
            ) from e
        try:
            # 20s timeout: pages that take longer are usually hung and not worth
            # blocking the agent loop on.
            response = requests.get(url, timeout=20)
            response.raise_for_status()

            # HTML -> markdown is cheaper for the model to read than raw HTML
            # and strips most layout noise.
            markdown_content = markdownify(response.text).strip()

            # Collapse runs of 3+ blank lines so pages with heavy whitespace do
            # not blow the token budget.
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

            # Hard cap: smolagents.utils.truncate_content keeps the head/tail
            # and inserts a marker in the middle.
            return truncate_content(markdown_content, 10000)

        except requests.exceptions.Timeout:
            return "The request timed out. Please try again later or check the URL."
        except RequestException as e:
            return f"Error fetching the webpage: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def __init__(self, *args, **kwargs):
        self.is_initialized = False
