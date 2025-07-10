import os
from functools import lru_cache
from ollama import Client

@lru_cache
def _client() -> Client:
    return Client(
        host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        verify=os.getenv("OLLAMA_VERIFY_SSL", "true").lower() == "true",
        timeout=120
    )

def generate(prompt: str, model: str = "llama3.1:8b") -> str:
    resp = _client().generate(model=model, prompt=prompt, stream=False)
    return resp["response"]

def chat(messages: list, model: str = "llama3.1:8b") -> str:
    resp = _client().chat(model=model, messages=messages, stream=False)
    return resp["message"]["content"]
