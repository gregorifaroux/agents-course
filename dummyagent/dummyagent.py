"""Minimal manual tool-use loop against a local Ollama model.

No framework. We feed the LLM a ReAct-style system prompt, stop it before it
hallucinates an observation, run the "tool" ourselves in Python, splice the
real result back into the conversation, and let the model finish.

This file exists to show what smolagents / LangChain do under the hood.
"""
from huggingface_hub import InferenceClient


# Stand-in for a real tool. Returns a nonsense sentinel so you can tell
# whether the final answer actually used the tool output or made one up.
def get_weather(location):
    return f"the weather in {location} is zorblax-42. \n"

# System Prompt
SYSTEM_PROMPT = """Answer the following questions as best you can. You have access to the following tools:

get_weather: Get the current weather in a given location

The way you use the tools is by specifying a json blob.
Specifically, this json should have an `action` key (with the name of the tool to use) and an `action_input` key (with the input to the tool going here).

The only values that should be in the "action" field are:
get_weather: Get the current weather in a given location, args: {"location": {"type": "string"}}
example use :

{{
  "action": "get_weather",
  "action_input": {"location": "New York"}
}}


ALWAYS use the following format:

Question: the input question you must answer
Thought: you should always think about one action to take. Only one action at a time in this format:
Action:

$JSON_BLOB (inside markdown cell)

Observation: the result of the action. This Observation is unique, complete, and the source of truth.
(this Thought/Action/Observation can repeat N times, you should take several steps when needed. The $JSON_BLOB must be formatted as markdown and only use a SINGLE action at a time.)

You must always end your output with the following format:

Thought: I now know the final answer
Final Answer: the final answer to the original input question

Now begin! Reminder to ALWAYS use the exact characters `Final Answer:` when you provide a definitive answer. """

# Ollama exposes an OpenAI-compatible endpoint at /v1, so the HF
# InferenceClient works against it unchanged.
client = InferenceClient(base_url="http://127.0.0.1:11434/v1")

# Step 1: ask the model, and stop generation the moment it writes
# "Observation:". Without the stop token the model would happily invent its
# own weather reading right after the Action block.
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "What's the weather in London?"},
]

output = client.chat.completions.create(
    model="qwen2:7b",
    messages=messages,
    stream=False,
    max_tokens=200,
    stop=["Observation:"],
)
print(output.choices[0].message.content)

# Step 2: execute the tool in real Python, splice the result into the
# assistant turn after the "Observation:" marker, then let the model continue
# and produce its Final Answer from the real tool output.
messages.append({
    "role": "assistant",
    "content": output.choices[0].message.content + "Observation:\n" + get_weather("London"),
})

output = client.chat.completions.create(
    model="qwen2:7b",
    messages=messages,
    stream=False,
    max_tokens=200,
)
print(output.choices[0].message.content)
