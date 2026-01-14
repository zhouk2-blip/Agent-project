from __future__ import annotations
from typing import Any, Dict

from .gamil_provider import GmailProvider, GmailOAuthConfig

def build_email_provider(cfg: Dict[str, Any]):
    email_cfg = cfg.get("email", {})
    default_name = email_cfg.get("default_provider", "gmail")
    providers = email_cfg.get("providers", {})
    p = providers.get(default_name)

    if not p:
        raise ValueError(f"No email provider config for '{default_name}'")

    ptype = p.get("type")
    if ptype == "gmail_oauth":
        return GmailProvider(GmailOAuthConfig(
            credentials_path=p["credentials_path"],
            token_path=p["token_path"],
        ))

    raise ValueError(f"Unknown email provider type: {ptype}") 