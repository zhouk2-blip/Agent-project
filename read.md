# Agent-Project
A local, Python-based multi-agent assistant that runs on your machine.  
The system currently supports:
- A **QA agent** powered by a local LLM
- An **Email agent** integrated with Gmail (draft → revise → confirm → send)
- A central **Orchestrator** that routes user input and manages session state
> Current version is designed for **Windows** only.
---
## What This Project Does
This project implements a **simple but explicit multi-agent architecture**.
At runtime:
1. User input is sent to a central **Orchestrator**
2. The orchestrator:
   - Parses the command (rule-based)
   - Routes it to the appropriate agent
   - Maintains session state (email drafts, pending confirmations)
3. Agents call tools (LLM, Gmail API, editor) to complete the task
There are currently **two agents**:
### QAAgent
- Handles general questions
- Uses a **local LLM via Ollama**
- Responds in the same language as user input
### EmailAgent
- Summarizes recent Gmail inbox messages
- Drafts emails using an LLM
- Saves drafts directly to **Gmail Drafts**
- Supports:
  - LLM-based editing
  - LLM-based rewriting
  - Manual editing via VS Code
- Requires **explicit confirmation** before sending any email
Emails are **never sent automatically**.
---

## System Architecture
```text
User
 ↓
Orchestrator
  ├─ State Gate (confirm send)
  ├─ Parser (rule-based)
  ├─ Router (email / QA)
 ↓
Agent (EmailAgent or QAAgent)
 ↓
Tools (LLM via Ollama, Gmail API, VS Code)
---

## Prerequisite
Python 3.10 or higher

Optional but recommended:
create a new virtual environment:
python -m venv agent-env
agent-env\Scripts\activate

### Python Dependencies:
pip install google-api-python-client google-auth google-auth-oauthlib requests


This project uses Ollama to run llm locally:
install ollama: https://ollama.com
pull a model: ollama pull llama3

Gmail API Access (EmailAgent Only)
To use email features, you need:
A Gmail account
Access to Google Cloud Console
Setup steps:
1. Create a Google Cloud project
2. Enable Gmail API
3. Configure OAuth consent screen:
    User type: External
    Add yourself as a test user, example@school.edu
4. Add scopes:
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.compose
5. create an OAuth client and download the Json file
6. rename it to: gmail_credentials.json 
7. place it in :secrets/gmail_credentials.json
---

## VScode(optional):
Used for manual email editing.
Install Visual Studio Code
Enable code command in PATH
Ctrl + Shift + P
→ Shell Command: Install 'code' command in PATH
---

##Running the project:
python-m run_orchestrator.py
On first run:
A browser window opens for Gmail OAuth
You log in and grant permission
Token is saved locally
---

##draft an email:
草拟邮件 to=xxx@school.edu subject="trial" 内容="have you finished dinner?"


