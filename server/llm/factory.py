from .ollama_provider import OllamaProvider

def build_provider(cfg:dict):
    llm = cfg['llm']
    if llm.get('provider') == 'ollama':
        return OllamaProvider(
            base_url=llm ['base_url'],
            model = llm['model'],
            time_out_s= int(llm.get('time_out_s',120)),
            temperature = float(llm.get('temperature',0.3))
        )
    raise ValueError(f"Unknown provider: {llm.get('provider')}")
