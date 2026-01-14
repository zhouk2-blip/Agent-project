from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import List, Optional

from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from .base import EmailHeader

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]
#headers = [
#{"name": "From", "value": "Alice <alice@gmail.com>"},
#{"name": "To", "value": "Bob <bob@gmail.com>"},
#{"name": "Subject", "value": "Hello"},]
def _get_header(headers: list[dict],name: str)-> str:
    name_l = name.lower()
    for h in headers:
        if(h.get("name") or "").lower() == name_l:
            return h.get("value")or ""
    return ""

@dataclass
class GmailOAuthConfig:
    credentials_path :str
    token_path: str

class GmailProvider:
    name = "gmail"

    def __init__(self,cfg:GmailOAuthConfig):
        self.cfg = cfg
        self.service = self._build_service()
    
    def _build_service(self):
        creds :Credentials |None = None
        
        try:
            creds = Credentials.from_authorized_user_file(self.cfg.token_path, SCOPES)
        except Exception:
            creds = None 
        
        #refresh/login
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not creds or not creds.valid: 
            flow = InstalledAppFlow.from_client_secrets_file(self.cfg.credentials_path,SCOPES) #a process controller of OAuth authorization
            #local server auth: opens brower once
            creds = flow.run_local_server(port =0)
            #flow(once)-> Credentials(long term)

        #save token
        with open(self.cfg.token_path,'w',encoding = 'utf-8') as f:
            f.write(creds.to_json())
        
        return build("gmail", "v1", credentials= creds)
    
    def list_latest(self, limit: int = 10, query: Optional[str] = None, days: Optional[int] = None) -> List[EmailHeader]:
        user_id = "me"
        q_parts = []
        if days is not None:
            q_parts.append(f"newer_than:{days}d")
        if query:
            q_parts.append(query)
        q = "".join(q_parts).strip()
        resp  = self.service.users().messages().list(
            userId = user_id, 
            q=q, 
            labelIds = ["INBOX"],
            includeSpamTrash = False,
            maxResults= limit).execute()
        msgs = resp.get("messages", []) or []

        out: List[EmailHeader] = []
        for m in msgs:
            msg_id = m["id"]
            full = self.service.users().messages().get( 
                userId = user_id,
                id = msg_id,
                format = "metadata",
                metadataHeaders = ["From","Subject","Date"],
            ).execute()
            headers = full.get("payload",{}).get("headers",[])or []
            out.append(EmailHeader(
                id = full.get("id",msg_id),
                thread_id = full.get("threadId"),
                from_ = _get_header(headers,"From"),
                subject=_get_header(headers, "Subject"),
                date=_get_header(headers, "Date"),
                snippet=full.get("snippet", "") or "",
            ))
        return out
    def create_draft(self, to: str, subject: str, body: str) -> str:
        user_id = "me"

        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        # From can be omitted; Gmail sets it automatically for "me"
        msg.set_content(body)

        raw_bytes = msg.as_bytes()
        raw_b64 = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

        draft_body = {"message": {"raw": raw_b64}}
        draft = self.service.users().drafts().create(userId=user_id, body=draft_body).execute()
        return draft.get("id")
    def send_draft (self, draft_id: str)-> str:
        user_id = "me"
        resp = self.service.users().drafts().send(
            userId =user_id,
            body={"id": draft_id}
        ).execute()
        return resp.get("id", "")
    def update_draft(self, draft_id: str, to: str, subject: str, body: str) -> str:
        user_id = "me"

        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        raw_bytes = msg.as_bytes()
        raw_b64 = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

        # drafts.update 需要包含 id + message.raw
        draft_body = {
            "id": draft_id,
            "message": {"raw": raw_b64},
        }

        draft = self.service.users().drafts().update(
            userId=user_id,
            id=draft_id,
            body=draft_body
        ).execute()

        return draft.get("id", draft_id)
