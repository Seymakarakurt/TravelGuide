# ai_service.py
import os
from functools import lru_cache
from ollama import Client

@lru_cache  # Singleton, damit nicht jedes Mal ein neuer HTTP-Pool entsteht
def _client() -> Client:
    return Client(
        host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        verify=os.getenv("OLLAMA_VERIFY_SSL", "true").lower() == "true",
        timeout=120  # Sekunden
    )

def generate(prompt: str, model: str = "llama3:8b") -> str:
    """Einmalige Vervollständigung."""
    resp = _client().generate(model=model, prompt=prompt, stream=False)
    return resp["response"]

def chat(messages: list, model: str = "llama3:8b") -> str:
    """Mehrturn-Chat. messages = [{'role':'user','content': ...}, …]"""
    resp = _client().chat(model=model, messages=messages, stream=False)
    return resp["message"]["content"]
