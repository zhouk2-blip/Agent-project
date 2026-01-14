# server/state.py  base
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal

@dataclass
class DraftState:
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    version: int = 0
    source: Literal["llm", "human", "mixed"] = "llm"
    draft_id: Optional[str] = None

@dataclass
class SessionState:
    draft: Optional[DraftState] = None
    pending_send: bool = False #pending state