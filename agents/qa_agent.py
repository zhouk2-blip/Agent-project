from __future__ import annotations
from typing import List, Dict 
from server.llm.base import LLMProvider, Message
from .base import AgentResult

class QAAgent:
    name = 'qa'

    def __init__(self,provider: LLMProvider):
        self.provider = provider 

    def handle(self, user_text: str) -> AgentResult:
        messages: List [Message] = [
            {'role':'system','content':'you are an local Ai assistant, give users response in the same language as their input.'},
            {'role':'user','content': user_text},
        ]
        resp = self.provider.chat(messages)
        return AgentResult(content = resp.content, messages = messages)