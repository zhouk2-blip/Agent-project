import requests
BASE_URL = "http://127.0.0.1:11434"
MODEL = "llama3.1:8b"

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "you are an ai assistant, answer questions in user's languages."},
        {"role": "user", "content": "你好，请用一句话证明你能正常工作。"}
    ],
    "stream": False
}

r = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=120)
r.raise_for_status()
data = r.json()
print(data["message"]["content"])