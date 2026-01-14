import os,sys
import yaml
from server.llm.factory import build_provider

def load_cfg():
    with open("configs/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    text = "怎么注释掉一大段代码"
    cfg = load_cfg()
    provider = build_provider(cfg)

    messages = [
        {"role": "system", "content": "you are an ai assistant, answer questions in user's languages."},
        {"role": "user", "content": text},
    ]
    resp = provider.chat(messages)
    print(resp.content)

if __name__ == "__main__":
    main()
