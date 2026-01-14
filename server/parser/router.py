# server/parser/router.py
from __future__ import annotations
from .schema import Action, ParsedCommand

def parse_user_text(user_text: str) -> ParsedCommand:
    t = (user_text or "").strip()
    if not t:
        return ParsedCommand(action=Action.HELP, args={}, confidence=0.0)

    low = t.lower()

    # show / help / cancel / send
    if low in ("help", "h", "?"):
        return ParsedCommand(Action.HELP, {})
    if low in ("show", "ls", "view", "print"):
        return ParsedCommand(Action.SHOW, {})
    if low in ("cancel", "c", "quit", "q", "exit"):
        return ParsedCommand(Action.CANCEL, {})
    if low in ("send", "s"):
        return ParsedCommand(Action.SEND, {})

    # revise family
    tokens = t.split()
    head = tokens[0].lower()

    # Allow short commands
    if head in ("manual",):
        return ParsedCommand(Action.REVISE, {"mode": "manual", "instruction": ""})
    if head in ("edit",):
        instr = t[len(tokens[0]):].strip()
        return ParsedCommand(Action.REVISE, {"mode": "edit", "instruction": instr})
    if head in ("rewrite", "regenerate", "regen"):
        instr = t[len(tokens[0]):].strip()
        return ParsedCommand(Action.REVISE, {"mode": "regenerate", "instruction": instr})

    # Explicit "revise <mode> <instruction...>"
    if head in ("revise", "r"):
        mode = tokens[1].lower() if len(tokens) >= 2 else "edit"
        instr = " ".join(tokens[2:]).strip() if len(tokens) >= 3 else ""
        # normalize
        if mode in ("m", "manual"):
            mode = "manual"
        elif mode in ("e", "edit"):
            mode = "edit"
        elif mode in ("re", "rewrite", "regenerate", "regen"):
            mode = "regenerate"
        else:
            # unknown mode, treat as edit instruction
            instr = " ".join(tokens[1:]).strip()
            mode = "edit"
        return ParsedCommand(Action.REVISE, {"mode": mode, "instruction": instr})

    # fallback: treat as NEW_EMAIL (keep your old to=/subject= parser inside orchestrator)
    return ParsedCommand(Action.NEW_EMAIL, {"raw": t}, confidence=0.5)
