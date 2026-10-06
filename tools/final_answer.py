"""smolagents Tool used by an agent to signal it is done and return its answer."""
from typing import Any, Optional
from smolagents.tools import Tool


class FinalAnswerTool(Tool):
    """Identity tool. Calling it is how a CodeAgent exits its reasoning loop.

    smolagents treats a call to the tool named `final_answer` as the terminal
    step: whatever is passed as `answer` becomes the agent's return value.
    """

    name = "final_answer"
    description = "Provides a final answer to the given problem."
    inputs = {'answer': {'type': 'any', 'description': 'The final answer to the problem'}}
    output_type = "any"

    def forward(self, answer: Any) -> Any:
        return answer

    def __init__(self, *args, **kwargs):
        self.is_initialized = False
