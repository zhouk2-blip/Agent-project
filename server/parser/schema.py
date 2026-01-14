# server/parser/schema.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

class Action(str, Enum):
    NEW_EMAIL = "NEW_EMAIL"
    REVISE = "REVISE"
    SEND = "SEND"
    SHOW = "SHOW"
    CANCEL = "CANCEL"
    HELP = "HELP"

@dataclass
class ParsedCommand:
    action: Action
    args: Dict[str, Any]
    confidence: float = 1.0
