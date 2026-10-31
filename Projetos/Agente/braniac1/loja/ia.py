# -*- coding: utf-8 -*-
"""IA SO por API (o notebook da loja e fraco: nada de modelo local). Tenta cada provedor gratis em ordem, pula os sem cota.

Chaves em config.ini, secao [ia] (chaves proprias da loja). Sem nenhuma chave ou com todas sem cota: devolve None e a Layla
usa so mensagens-padrao e avisa a equipe. Nunca manda dado de pagamento: quem chama ja filtra isso antes.
"""
import time

PROVEDORES = [  # (nome, url, modelo, chave no config)
    ("gemini", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-flash-latest", "gemini"),
    ("gemini-lite", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-3.1-flash-lite", "gemini"),
    ("gemini-b", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-flash-latest", "gemini2"),
    ("gemini-lite-b", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-3.1-flash-lite", "gemini2"),
    ("groq", "https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-120b", "groq"),
    ("groq-20b", "https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-20b", "groq"),
    ("openrouter", "https://openrouter.ai/api/v1/chat/completions", "nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter"),
    ("openrouter-gemma", "https://openrouter.ai/api/v1/chat/completions", "google/gemma-4-31b-it:free", "openrouter"),
]
_descanso = {}
ULTIMO = ""


LOCAL_URL = "http://127.0.0.1:11434/api/chat"


def _local(mensagens, modelo, timeout):
    """Ultimo recurso: IA local (Ollama), so se estiver instalada e ligada. Devolve texto ou None."""
    import requests
    global ULTIMO
    if not modelo:
        return None
    try:
        r = requests.post(LOCAL_URL, timeout=timeout, json={"model": modelo, "messages": mensagens, "stream": False, "keep_alive": "2m",
                                                              "options": {"temperature": 0.4, "num_ctx": 2048, "num_predict": 220}})
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    txt = ((r.json().get("message") or {}).get("content") or "").strip()
    if txt:
        ULTIMO = "local:" + modelo
    return txt or None


def status(chaves):
    """[(nome, estado)] de cada provedor, para o painel. estado: 'ok' | 'sem chave' | 'em descanso'."""
    out = []
    for nome, _u, _m, ch in PROVEDORES:
        if not (chaves.get(ch) or "").strip():
            out.append((nome, "sem chave"))
        elif _descanso.get(nome, 0) > time.time():
            out.append((nome, "em descanso"))
        else:
            out.append((nome, "ok"))
    return out


def local_disponivel(modelo, timeout=2):
    import requests
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=timeout)
        return r.status_code == 200 and any(m.get("name", "").split(":")[0] == (modelo or "").split(":")[0] for m in r.json().get("models", []))
    except (requests.RequestException, ValueError):
        return False


def completar(mensagens, chaves, timeout=40, max_tokens=400):
    """mensagens = [{'role','content'}]. chaves = {'gemini': '...', ...}. Devolve o texto ou None se nenhum provedor respondeu."""
    import requests
    global ULTIMO
    for nome, url, modelo, ch in PROVEDORES:
        chave = (chaves.get(ch) or "").strip()
        if not chave or _descanso.get(nome, 0) > time.time():
            continue
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {chave}"}, timeout=timeout,
                              json={"model": modelo, "messages": mensagens, "temperature": 0.5, "max_tokens": max_tokens})
        except requests.RequestException:
            _descanso[nome] = time.time() + 120
            continue
        if r.status_code != 200:
            _descanso[nome] = time.time() + (900 if r.status_code == 429 else 180)
            continue
        try:
            txt = (r.json()["choices"][0]["message"].get("content") or "").strip()
        except (KeyError, IndexError, ValueError):
            txt = ""
        if txt:
            ULTIMO = nome
            return txt
    return _local(mensagens, (chaves.get("local_modelo") or "").strip(), 120)
