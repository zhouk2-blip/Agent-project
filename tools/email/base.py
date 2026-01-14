from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, List, Optional

@dataclass
class EmailHeader:
    id: str
    thread_id :str |None
    from_: str
    subject: str
    date: str
    snippet: str

class EmailProvider(Protocol):
    name: str

    def list_latest(self,limit:int =5, query: Optional[str]=None) ->List[EmailHeader]:
        ...
    
    def create_draft(self, to: str, subject: str, body: str) -> str:
        '''return draft_id'''
        ...
    def send_draft (self, draft_id: str) ->str:
        "send a draft and return message_id"
        ...
    def update_draft(self, draft_id: str, to: str, subject: str, body: str) -> None:
        ...