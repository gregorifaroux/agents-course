from smolagents import LiteLLMModel

model = LiteLLMModel(
	model_id="ollama_chat/qwen2:7b",
	api_base="http://127.0.0.1:11434",
	num_ctx=8192,
)
messages = [{"role": "user", "content": [{"type": "text", "text": "Say hi in five words in English and then French."}]}]
print(model(messages).content)
messages = [{"role": "user", "content": [{"type": "text", "text": "You are a rebel service agent that loves to swear. Say hi in ten words in English and then French."}]}]
print(model(messages).content)

