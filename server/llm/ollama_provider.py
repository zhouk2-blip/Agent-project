import requests 
from typing import List, Optional, Dict, Any
from .base import LLMResponse, Message

class OllamaProvider:
    def __init__(self, base_url:str, model:str, time_out_s: int = 120, temperature: float=0.2):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout_s = time_out_s
        self.temperature =temperature
    def chat(self, messages: List[Message], *, temperature: Optional[float]=None, max_tokens: Optional[int]=None) -> LLMResponse:
        temp = self.temperature if temperature is None else temperature
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temp},
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()
        return LLMResponse(content=data["message"]["content"], raw=data)