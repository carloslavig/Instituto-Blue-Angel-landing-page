# -*- coding: utf-8 -*-
"""Liga/desliga da Layla pelo painel (sobrevive a reiniciar o programa). dados/controle.json."""
import json
from pathlib import Path

ARQ = Path(__file__).resolve().parent.parent / "dados" / "controle.json"


def ler():
    try:
        d = json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: bool(v) for k, v in d.items() if k in ("responder", "feedback")}


def gravar(**kw):
    atual = ler()
    atual.update({k: bool(v) for k, v in kw.items() if k in ("responder", "feedback")})
    ARQ.parent.mkdir(exist_ok=True)
    ARQ.write_text(json.dumps(atual), encoding="utf-8")
    return atual


ARQ_EQUIPE = Path(__file__).resolve().parent.parent / "dados" / "equipe.json"


def ler_equipe():
    """Nomes (como aparecem no WhatsApp da loja) de quem a Layla consulta quando nao sabe: ex. Raissa, Gabi."""
    try:
        return [str(x).strip() for x in json.loads(ARQ_EQUIPE.read_text(encoding="utf-8")) if str(x).strip()]
    except (OSError, ValueError):
        return []


def gravar_equipe(nomes):
    ARQ_EQUIPE.parent.mkdir(exist_ok=True)
    ARQ_EQUIPE.write_text(json.dumps([n.strip() for n in nomes if n.strip()], ensure_ascii=False), encoding="utf-8")
