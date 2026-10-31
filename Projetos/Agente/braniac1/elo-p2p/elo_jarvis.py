# -*- coding: utf-8 -*-
"""Layla -> Jarvis pelo elo P2P (par_webrtc). falar(tipo, texto) devolve a resposta do Jarvis (str) ou None se o canal estiver fora:
nesse caso quem chamou segue pelo WhatsApp, exatamente como antes. O registro da conversa fica no Braniac do Carlos."""
import json
from pathlib import Path

from . import par_webrtc

RAIZ = Path(__file__).resolve().parent.parent
_P = [None]


def falar(tipo, texto, timeout=75):
    try:
        if _P[0] is None:
            _P[0] = par_webrtc.Par(RAIZ / "dados", "loja", lambda de, t: "")
        r = _P[0].pedir({"texto": json.dumps({"tipo": str(tipo)[:30], "texto": str(texto)[:1800]}, ensure_ascii=False)}, timeout)
        return str(r[0].get("texto", "")).strip() or None
    except Exception:
        return None
