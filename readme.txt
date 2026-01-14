User
 ↓
Orchestrator
  ├─ State Gate (confirm_send)
  ├─ Parser (action detection)
  ├─ Router (email vs QA)
 ↓
Agent (EmailAgent / QAAgent)
 ↓
Tools (LLM, Gmail API, Editor)


email_agent setup:
log in our google cloud console
go to APIs & Services and enable gmail api
go to OAuth consent screen
go to audience, set user type to external, add test user : your email: example@school.edu
go to data access: add scopes:
https://www.googleapis.com/auth/gmail.readonly;
https://www.googleapis.com/auth/gmail.modify;
https://www.googleapis.com/auth/gmail.send;
https://www.googleapis.com/auth/gmail.compose;

then, you are ready to create the client, and download the json file.  Rename it to gmail_credentials.json and put it in the secrets folder. The gmail_token.json will be generated after you run the system.

In v1, you have to pull the model from Ollama according to your demand.

在没有parser的情况下，发送email指令：
草拟邮件 to=xxx@school.edu subject="trial" 内容="have you finished dinner?"

structure：
AGENT-PROJECT/
├─ agents/
│  ├─ __init__.py
│  ├─ base.py
│  ├─ email_agent.py
│  └─ qa_agent.py
├─ apps/
├─ configs/
│  └─ config.yaml
├─ docs/
├─ memory/
├─ scripts/
│  ├─ __init__.py
│  ├─ new_test.py
│  ├─ run_orchestrator.py
│  └─ test.py
├─ secrets/
│  ├─ gmail_credentials.json
│  └─ gmail_token.json
├─ server/
│  ├─ __init__.py
│  ├─ orchestrator.py
│  ├─ llm/
│  │  ├─ __init__.py
│  │  ├─ base.py
│  │  ├─ factory.py
│  │  └─ ollama_provider.py
│  ├─ tools/
│  |  ├─ __init__.py
│  |  └─ email/
│  |     ├─ __init__.py
│  |     ├─ base.py
│  |     ├─ factory.py
│  |     └─ gmil_provider.py
|  |
|  ├─ parser/
|  |  ├─ __init__.py
│  │  ├─ schema.py
│  │  ├─ router.py
│  │  


