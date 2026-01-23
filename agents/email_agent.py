from __future__ import annotations
from typing import List, Dict, Tuple
from server.llm.base import LLMProvider, Message
from .base import AgentResult
from tools.email.base import EmailProvider, EmailHeader
import json
import re
def _extract_email_local(text: str) -> str:
        m = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, flags=re.IGNORECASE)
        return m.group(0) if m else ""

class EmailAgent:
    name = "email"

    def __init__(self, provider: LLMProvider, email_provider: EmailProvider, profile: dict):
        self.llm = provider
        self.mail = email_provider
        self.profile = profile
    
    def summarize_inbox(self, days: int = 7 , limit: int = 10) -> AgentResult:
        emails = self.mail.list_latest(limit=limit, days = days)
        emails = self.rank_emails(emails)
        emails = emails [:5]
        lines = []
        for i, e in enumerate(emails, start=1):
            lines.append(
                f"{i}. From: {e.from_}\n"
                f"   Date: {e.date}\n"
                f"   Subject: {e.subject}\n"
                f"   Snippet: {e.snippet}\n"
            )
        inbox_text = "\n".join(lines) if lines else "no email received"

        messages: List[Message] = [
            {"role": "system", "content": (
                "你是一个邮件助理。请用中文完成：\n"
                "1) 总结最近邮件要点, 邮件内的重要的信息（时间，任务，紧急程度）；\n"
                "2) 标出最重要的 1-3 封（说明理由）；\n"
                "3) 给出可执行下一步（要不要回、回什么）。\n"
                "输出用条目列表，简洁清晰。"
            )},
            {"role": "user", "content": f"这是我最近的邮件列表：\n\n{inbox_text}"},
        ]
        resp = self.llm.chat(messages)
        return AgentResult(content=resp.content, messages=messages)
    
    

    def draft_email(self, to: str, subject: str, intent: str, context: str = "") -> Tuple[AgentResult, str]:
        name = self.profile.get("display_name", "Jason")
        sig = self.profile.get("email_signature", f"Best regards,\n{name}")
        default_lang = (self.profile.get("default_email_language") or "en").lower()
       
        messages: List[Message] = [
            {"role": "system", "content": (
                "You are a professional email writing assistant.\n"
                "Write a concise, polite email body.\n"
                "Rules:\n"
                "- Do NOT invent facts; if missing info, write [NEEDS USER INPUT: ...]\n"
                f"- Default language: {default_lang} (use English unless user explicitly wants Chinese)\n"
                f"- Sender name is {name}\n"
                "- The email must end with the signature EXACTLY as provided below:\n"
                f"{sig}\n"
                "- Output ONLY the email body (no To/Subject)."
            )},
            {"role": "user", "content": (
                f"To: {to}\n"
                f"Subject: {subject}\n"
                f"Intent: {intent}\n"
                f"Context (optional): {context}\n"
                "Generate the email body now."
            )},
        ]
        resp = self.llm.chat(messages)

        draft_id = self.mail.create_draft(to=to, subject=subject, body=resp.content)

        # 注意：这里只创建草稿，不发送
        return AgentResult(
            content=resp.content,
            messages=messages,
        ), draft_id
    def rank_emails (self, emails:list[EmailHeader])->list[EmailHeader]:
        """
        先做一个简单规则版，后续接 memory：
        - memory 里可存：重要联系人/关键词/课程名/教授邮箱等
        """
        important_senders = set(self.profile.get("important_senders", []))  
        important_keywords = set(self.profile.get("important_keywords", []))

        def score(e: EmailHeader) -> int:
            s = 0
            if any(x in (e.from_ or "") for x in important_senders):
                s += 5
            subj = (e.subject or "").lower()
            if any(k.lower() in subj for k in important_keywords):
                s += 3
           
            for kw in ["urgent", "asap", "deadline", "due", "quiz", "midterm", "final"]:
                if kw in subj:
                    s += 2
            return s

        return sorted(emails, key=score, reverse=True)
    # agents/email_agent.py  (add these methods inside EmailAgent)

    def edit_draft_body(self, current_body: str, instruction: str, to: str | None = None, subject: str | None = None) -> str:
        name = self.profile.get("display_name", "Jason")
        sig = self.profile.get("email_signature", f"Best regards,\n{name}")
        prompt = f"""
            You are editing an email draft.

            Return ONLY the revised email body. No commentary.

            Constraints:
            - Keep it as a complete email (greeting, body, closing).
            - Preserve meaning unless the instruction asks to change meaning.
            - Keep names, dates, and facts consistent.
            
            User signature (use exactly, including line breaks):
            {sig}
            Context:
            To: {to or ""}
            Subject: {subject or ""}

            Current draft:
            {current_body}

            Instruction:
            {instruction}
            """.strip()

        resp = self.llm.chat([{"role": "user", "content": prompt}])
        return resp.content.strip()


    def regenerate_body(self, instruction: str, to: str | None = None, subject: str | None = None, reference_body: str | None = None) -> str:
        name = self.profile.get("display_name", "Jason")
        sig = self.profile.get("email_signature", f"Best regards,\n{name}")
        prompt = f"""
    You are rewriting an email from scratch.

    Return ONLY the email body. No commentary.

    Requirements:
    - Produce a complete email (greeting, body, closing).
    - Follow the user's rewrite requirements.
    - You may reference the original intent, but rewrite freely.

    User signature (use exactly, including line breaks):
    {sig}
    Context:
    To: {to or ""}
    Subject: {subject or ""}

    Original (for intent only):
    {reference_body or ""}

    Rewrite requirements:
    {instruction}
    """.strip()

        resp = self.llm.chat([{"role": "user", "content": prompt}])
        return resp.content.strip()
    def draft_email_auto(self, user_text: str, context: str = "") -> Tuple[AgentResult, str, str, str]:
  
        name = self.profile.get("display_name", "Jason")
        sig = self.profile.get("email_signature", f"Best regards,\n{name}")
        default_lang = (self.profile.get("default_email_language") or "en").lower()
        to_guess = _extract_email_local(user_text)
        messages: List[Message] = [
            {"role": "system", "content": (
                "You are a professional email assistant.\n"
                "Return STRICT JSON only (no markdown, no commentary).\n"
                "Schema:\n"
                "{\n"
                '  "to": string,\n'
                '  "subject": string,\n'
                '  "body": string\n'
                "}\n"
                "Rules:\n"
                "- Do NOT invent facts.\n"
                "- If recipient email is missing, set to \"\" and include [NEEDS USER INPUT: recipient email] in body.\n"
                f"- Default language: {default_lang}\n"
                "- The email must end with the signature EXACTLY as provided below:\n"
                f"{sig}\n"
            )},
            {"role": "user", "content": (
                f"User request:\n{user_text}\n\n"
                f"Context (optional): {context}\n"
                "Generate JSON now."
            )},
        ]

        resp = self.llm.chat(messages)
        raw = (resp.content or "").strip()

        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        json_text = m.group(0) if m else raw

        try:
            data = json.loads(json_text)
        except Exception:
            body = raw if raw else "[NEEDS USER INPUT: recipient email]"
            return AgentResult(content=body, messages=messages), "", "", ""

        to = (data.get("to") or "").strip()

        if not to and to_guess:
            to= to_guess
        subject = (data.get("subject") or "").strip()
        body = (data.get("body") or "").strip()

        if not to:
            if "[NEEDS USER INPUT" not in body:
                body = (body + "\n\n[NEEDS USER INPUT: recipient email]").strip()
            return AgentResult(content=body, messages=messages), "", "", subject
        if to and "[NEEDS USER INPUT: recipient email]" in body:
            body = body.replace("[NEEDS USER INPUT: recipient email]", "").strip()
        draft_id = self.mail.create_draft(to=to, subject=subject or "(no subject)", body=body)
        return AgentResult(content=body, messages=messages), draft_id, to, subject
