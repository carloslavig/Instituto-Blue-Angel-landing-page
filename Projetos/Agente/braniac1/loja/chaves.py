# -*- coding: utf-8 -*-
"""Chaves de API da loja: reconhece uma chave colada no chat, testa de verdade e guarda em dados/chaves.json.

Reconhece pelo formato: Gemini (AIza... ou AQ....), Groq (gsk_...), OpenRouter (sk-or-...). Uma segunda chave do Gemini
(outro projeto Google, com cota propria) vai para 'gemini2'. A chave NUNCA e repetida de volta no chat nem escrita no log.
"""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ = RAIZ / "dados" / "chaves.json"
CAMPOS = ("gemini", "gemini2", "groq", "openrouter")
PADROES = [
    ("openrouter", re.compile(r"sk-or-[A-Za-z0-9_\-]{20,}")),
    ("groq", re.compile(r"gsk_[A-Za-z0-9]{20,}")),
    ("gemini", re.compile(r"AIza[0-9A-Za-z_\-]{30,}")),
    ("gemini", re.compile(r"AQ\.[A-Za-z0-9_\-]{30,}")),
]
NOMES = {"gemini": "Gemini", "gemini2": "Gemini (2ª chave)", "groq": "Groq", "openrouter": "OpenRouter"}


def detectar(texto):
    """[(provedor, chave)] encontrados no texto, sem repetir."""
    achados, vistos = [], set()
    for prov, rx in PADROES:
        for m in rx.finditer(texto or ""):
            if m.group(0) not in vistos:
                vistos.add(m.group(0))
                achados.append((prov, m.group(0)))
    return achados


def carregar():
    try:
        d = json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    return {k: str(d.get(k, "")).strip() for k in CAMPOS}


def salvar(d):
    ARQ.parent.mkdir(exist_ok=True)
    ARQ.write_text(json.dumps({k: d.get(k, "") for k in CAMPOS}, ensure_ascii=False, indent=1), encoding="utf-8")


def testar(prov, chave, timeout=25):
    """(ok, motivo). Faz uma chamada minima de verdade."""
    import requests
    cfg = {"gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-flash-latest"),
           "groq": ("https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-20b"),
           "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "google/gemma-4-31b-it:free")}
    url, modelo = cfg["gemini" if prov == "gemini2" else prov]
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {chave}"}, timeout=timeout,
                          json={"model": modelo, "messages": [{"role": "user", "content": "diga ok"}], "max_tokens": 20})
    except requests.RequestException:
        return False, "sem internet ou o servidor não respondeu"
    if r.status_code == 200:
        return True, ""
    if r.status_code == 429:
        return True, "a chave é válida, mas está sem cota agora (guardei mesmo assim)"
    if r.status_code in (400, 401, 403):
        return False, "a chave foi recusada (confira se copiou inteira)"
    return False, f"o servidor respondeu com erro {r.status_code}"


def adicionar(texto, atuais, testador=testar):
    """Le as chaves coladas em `texto`, testa e atualiza o dict `atuais` (no lugar). Devolve a lista de frases para mostrar."""
    falas = []
    for prov, chave in detectar(texto):
        if chave in atuais.values():
            falas.append(f"Essa chave do {NOMES[prov]} eu já tinha.")
            continue
        alvo = prov
        if prov == "gemini" and atuais.get("gemini"):
            alvo = "gemini2"
        ok, motivo = testador(alvo, chave)
        if ok:
            atuais[alvo] = chave
            salvar(atuais)
            falas.append(f"Chave do {NOMES[alvo]} funcionando e guardada ✅" + (f" ({motivo})" if motivo else ""))
        else:
            falas.append(f"Não guardei a chave do {NOMES[alvo]}: {motivo}.")
    return falas


def mascarar(chave):
    return (chave[:4] + "…" + chave[-3:]) if chave and len(chave) > 12 else ("•••" if chave else "")
