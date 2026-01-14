#rules that all agents need to follow
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, List, Dict 

Message = Dict[str, str] #the way that the whole system present messages

@dataclass
class AgentResult:
    content: str
    messages: List[Message]|None = None # memory optional

class Agent(Protocol):
    name: str

    def handle(self,user_txt:str) -> AgentResult: #Agent = a user input -> turn into function "AgentResult"
        ...#Ellipsis, here represents protocol