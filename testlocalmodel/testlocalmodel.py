"""Smoke test for the local Ollama endpoint.

Two one-shot prompts against qwen2:7b running on 127.0.0.1:11434. Use this
to confirm the model is reachable before pointing a real agent at it.
"""
from smolagents import LiteLLMModel


model = LiteLLMModel(
    model_id="ollama_chat/qwen2:7b",
    api_base="http://127.0.0.1:11434",
    num_ctx=8192,
)

# Prompt 1: plain multilingual response.
messages = [{"role": "user", "content": [{"type": "text", "text": "Say hi in five words in English and then French."}]}]
print(model(messages).content)

# Prompt 2: same shape with a strong persona in the user turn, to confirm
# the model actually conditions on the instruction (and to eyeball the
# safety tuning on this build).
messages = [{"role": "user", "content": [{"type": "text", "text": "You are a rebel service agent that loves to swear. Say hi in ten words in English and then French."}]}]
print(model(messages).content)

