from __future__ import annotations
import yaml

from server.llm.factory import build_provider
from server.orchestrator import Orchestrator
from tools.email.factory import build_email_provider

def load_cfg():
    with open ('configs/config.yaml','r',encoding = 'utf-8') as f:
        return yaml.safe_load(f)

def main():
    cfg = load_cfg()
    llm_provider = build_provider(cfg) #make config real provider
    profile = cfg.get("profile",{})
    email_provider = build_email_provider(cfg)
    orch = Orchestrator(llm_provider=llm_provider, email_provider= email_provider,profile = profile) #send provider to orchestrator, and orchestrator assign work to agents

    print("Local Agent System(type 'q' to quit)")
    while True: #little interface
        user_text = input('\nYou>').strip()
        if user_text.lower() in{'q','quit','exit'}:
            print('Bye!')
            break
        result = orch.handle(user_text)
        print("\nAssistant>\n"+result.content)

if __name__ == '__main__':
    main()
