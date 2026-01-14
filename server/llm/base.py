from typing import Protocol, List, Dict, Optional
from dataclasses import dataclass
Message = Dict[str,str] #{"role":"...","content":'...'}

@dataclass
class LLMResponse:
    content:str # the output that agent need to pay attention to
    raw:dict|None = None

class LLMProvider(Protocol):
    def chat(
        self,
        messages:List[Message], # context:(system propmt, user input, optional history response)
        *,# force following parameters paasing by key words, ex: provider.chat(messages, temperature = 0.2) instead of provider.chat(messages, 0.2)
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse: ...