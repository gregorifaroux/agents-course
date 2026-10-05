from huggingface_hub import InferenceClient

# Dummy function
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

client = InferenceClient(base_url="http://127.0.0.1:11434/v1")

# Step 1: ask, and stop before the model invents a weather result
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

# Step 2: run the tool yourself, then hand the result back
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
