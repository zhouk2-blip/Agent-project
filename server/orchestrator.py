from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
import re

from agents.qa_agent import QAAgent
from agents.email_agent import EmailAgent
from agents.base import AgentResult
from server.llm.base import LLMProvider
from tools.email.base import EmailProvider
from server.state import SessionState, DraftState
from server.parser.router import parse_user_text
from server.parser.schema import Action
from server.state import DraftState


import subprocess
import tempfile
from pathlib import Path

def parse_kv(text: str, key: str) -> str:
    # 支持：key=value / key = value / key="value" / key = "value"
    pattern = rf"{key}\s*=\s*(\"[^\"]*\"|[^\s]+)"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return ""
    val = m.group(1).strip()
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    return val

def manual_edit_vscode(current_body: str, *, suffix: str = ".md") -> str | None:
    """
    Open current_body in VSCode for manual editing and return updated body.
    Requires VSCode CLI: code --wait
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / f"draft{suffix}"
        p.write_text(current_body, encoding="utf-8")

        candidates = [
            ["code", "--wait", "--reuse-window", str(p)],
            ["code.cmd", "--wait", "--reuse-window", str(p)],
        ]

        last = None
        for cmd in candidates:
            try:
                subprocess.run(cmd, check=True)
                last = None
                break
            except FileNotFoundError as e:
                last = e
                continue

        if last is not None:
            raise RuntimeError(
                "VSCode CLI not found. Fix:\n"
                "1) Open VSCode\n"
                "2) Ctrl+Shift+P\n"
                "3) Search: 'Shell Command: Install 'code' command in PATH'\n"
                "Then restart your terminal."
            ) from last

        new_body = p.read_text(encoding="utf-8")
        if not new_body or new_body == current_body.strip():
            return None
        return new_body
def show_current_draft(self):
    d = self.session.draft
    if not d or not d.body:
        print("（当前没有草稿）")
        return
    print("\n----- CURRENT DRAFT -----")
    print(f"To: {d.to or ''}")
    print(f"Subject: {d.subject or ''}")
    print(f"Version: v{d.version}  Source: {d.source}")
    print("-------------------------")
    print(d.body)
    print("-------------------------\n")


@dataclass
class Orchestrator:
    llm_provider: LLMProvider
    email_provider: EmailProvider
    profile: dict
    pending: Optional[dict] = None  # 用于确认发送

    def __post_init__(self):
        self.agents: Dict[str, object] = {
            "qa": QAAgent(self.llm_provider),
            "email": EmailAgent(self.llm_provider, self.email_provider, self.profile),
        }
        self.session = SessionState() #session state

    def handle_revise(self, mode: str, instruction: str = ""):
        email_agent = self.agents["email"]
        d = self.session.draft
        if d and d.draft_id:
            self.email_provider.update_draft(d.draft_id, d.to, d.subject, d.body)

        if not d or not d.body:
            print("没有可修改的草稿。先起草一封邮件。")
            return

        mode = (mode or "").strip().lower()
        

        # 1) manual (VSCode)
        if mode == "manual":
            new_body = manual_edit_vscode(d.body)
            if new_body is None:
                print("未修改（或已取消）。")
                return
            d.body = new_body
            d.version += 1
            d.source = "human" if d.source == "llm" else "mixed"
            if d and d.draft_id:
                self.email_provider.update_draft(d.draft_id, d.to, d.subject, d.body)
            print(f" 草稿已手动更新（v{d.version}）")
            return

        # 2) edit (LLM modifies current)
        if mode in ("edit", "edit_draft"):
            if not instruction.strip():
                instruction = input("请输入修改指令（例如：更正式、更短、删第二段...）： ").strip()
                if not instruction:
                    print("未提供修改指令。")
                    return
            d.body = email_agent.edit_draft_body(
                current_body=d.body,
                instruction=instruction,
                to=d.to,
                subject=d.subject,
            )
            d.version += 1
            d.source = "llm" if d.source == "llm" else "mixed"
            print(f"✔ 草稿已由 LLM 修改（v{d.version}）")
            return

        # 3) regenerate (LLM rewrites)
        if mode in ("regenerate", "rewrite", "regen"):
            if not instruction.strip():
                instruction = input("请输入重写要求（例如：更简短、更正式、强调我搞错deadline...）： ").strip()
                if not instruction:
                    instruction = "Rewrite the email with the same intent, concise and polite."
            d.body = email_agent.regenerate_body(
                instruction=instruction,
                to=d.to,
                subject=d.subject,
                reference_body=d.body,
            )
            d.version += 1
            d.source = "llm" if d.source == "llm" else "mixed"
            print(f"✔ 草稿已重写（v{d.version}）")
            return

        print(f"不支持的 revise mode: {mode}")

    def route(self, user_text: str) -> str:
        t = user_text.lower()
        if any(k in t for k in ["邮箱", "邮件", "收件箱", "inbox", "email", "mail", "draft", "草稿", "发送", "send"]):
            return "email"
        return "qa"

    def handle(self, user_text: str) -> AgentResult:
        user_text = (user_text or "").strip()

        
        if self.pending and self.pending.get("type") == "confirm_send":
            low = user_text.lower().strip()
            if low.startswith(("revise", "edit", "rewrite", "regenerate", "manual", "show")):
                #if following action, still email_agent mode
                pass
            else:
                if user_text.upper() in {"CONFIRM SEND", "CONFIRM", "YES", "Y"}:
                    draft_id = self.pending["draft_id"]
                    to = self.pending["to"]
                    subject = self.pending["subject"]
                    self.pending = None

                    msg_id = self.email_provider.send_draft(draft_id)#send email
                    return AgentResult(content=f" 已发送！(Message ID: {msg_id})\nTo: {to}\nSubject: {subject}")

                if user_text.upper() in {"CANCEL", "NO", "N"}:
                    self.pending = None
                    return AgentResult(content=" 已取消发送（草稿仍保留在 Gmail Drafts）。")

                return AgentResult(content=(
                    " 你正在确认发送邮件。\n"
                    "- 输入 `CONFIRM SEND` 立即发送\n"
                    "- 输入 `CANCEL` 取消发送\n"
                ))

        # 空输入：直接提示，不再调用模型（避免乱语言）
        if user_text == "":
            return AgentResult(content="（请输入你的问题或指令，例如：总结我的收件箱 / 草拟邮件 ...）")

        # 1) first parse, then route
        cmd = parse_user_text(user_text)
        print("DEBUG cmd.action=", cmd.action, type(cmd.action), "args=", getattr(cmd, "args", None))

        if cmd.action in {Action.REVISE, Action.SHOW, Action.SEND, Action.CANCEL, Action.HELP}:
            key = "email"
            agent = self.agents[key]
        else:
            key = self.route(user_text)
            agent = self.agents[key]

        # 2) Email 分支
        if key == "email":
             # NEW: parser for revise / send / show
            # ---- SHOW CURRENT DRAFT ----
            if cmd.action == Action.SHOW:
                d = self.session.draft
                if not d or not d.body:
                    return AgentResult(content="（当前没有草稿）")
                return AgentResult(content=(
                    f"----- CURRENT DRAFT -----\n"
                    f"To: {d.to}\n"
                    f"Subject: {d.subject}\n"
                    f"Version: v{d.version}\n\n"
                    f"{d.body}\n"
                    f"-------------------------"
                ))

            # ---- REVISE (manual / edit / regenerate) ----
            if cmd.action == Action.REVISE:
                mode = cmd.args.get("mode", "edit")
                instruction = cmd.args.get("instruction", "")
                self.handle_revise(mode, instruction)
                d = self.session.draft
                return AgentResult(content=(
                        f"✅ 草稿已更新（v{d.version}，source={d.source}）\n\n"
                        f"{d.body}"
                    ))

                    
            
            
            # 2.1 summarize inbox
            if any(k in user_text for k in ["总结", "收件箱", "inbox", "最近", "最新"]):
                return agent.summarize_inbox(limit=5)

            # 2.2 drafting
            # support drafting to=... subject=... 内容=...
            to = parse_kv(user_text, "to")
            subject = parse_kv(user_text, "subject")
            content = parse_kv(user_text, "内容") or parse_kv(user_text, "content")

            if ("草拟" in user_text or "draft" in user_text.lower()) and to and subject:
                (draft_result, draft_id) = agent.draft_email(
                    to=to,
                    subject=subject,
                    intent=content,
                    context=""
                )

                #  NEW：把草稿正文写进 session（source of truth）
                self.session.draft = DraftState(
                    to=to,
                    subject=subject,
                    body=draft_result.content,
                    draft_id = draft_id,
                    version=1,
                    source="llm",
                )

                # 保留你原来的 pending（完全不动）
                self.pending = {
                    "type": "confirm_send",
                    "draft_id": draft_id,
                    "to": to,
                    "subject": subject,
                }

                return AgentResult(content=(
                    "✅ 已创建 Gmail 草稿，并生成如下正文：\n\n"
                    f"{draft_result.content}\n\n"
                    "你可以：\n"
                    "- 手动修改：revise manual\n"
                    "- 让 AI 改：revise edit 更正式一点\n"
                    "- 让 AI 重写：revise regenerate 更短版本\n"
                    "- 查看草稿：show\n\n"
                    "发送：CONFIRM SEND\n"
                    "取消：CANCEL\n"
                ))


            return AgentResult(content=(
                "EmailAgent 已启用。\n\n用法：\n"
                "1) 总结收件箱：总结我的收件箱\n"
                "2) 草拟并进入发送确认：草拟邮件 to=xxx subject=\"yyy\" 内容=\"zzz\"\n"
                "确认发送：CONFIRM SEND\n"
                "取消发送：CANCEL\n"
            ))

        # 3) QA 分支
        return agent.handle(user_text)

