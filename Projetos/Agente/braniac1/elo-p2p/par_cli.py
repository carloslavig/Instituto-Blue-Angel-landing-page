# -*- coding: utf-8 -*-
"""Parear este Braniac Loja com o do Carlos (uso: python -m loja.par_cli parear CODIGO | painel [sim|nao] | falar | status).
O codigo vem do Braniac do Carlos (ferramenta 'rede' acao par_codigo, nome 'loja'). O painel so fica visivel para ele depois de 'painel sim'."""
import sys
from pathlib import Path

from . import par_webrtc

RAIZ = Path(__file__).resolve().parent.parent


def main(a):
    p = par_webrtc.Par(RAIZ / "dados", "loja", lambda de, t: "", "")
    cmd = a[0] if a else "status"
    try:
        if cmd == "parear":
            p.parear(a[1], "jarvis")
            print("Pareado com o Braniac do Carlos. Agora rode: painel sim  (para ele ver o painel desta loja) e reinicie o Braniac Loja (LIGAR.bat).")
        elif cmd == "painel":
            p.permitir_painel(not (len(a) > 1 and a[1].lower() in ("nao", "não", "false", "0")))
            print("Painel:", "liberado para o Braniac do Carlos (so leitura)" if p.info()["painel"] else "bloqueado")
        elif cmd == "painel_porta":
            p.definir_painel_porta(a[1])
            print("O Braniac do Carlos passa a ver a tela da porta", a[1])
        elif cmd == "falar":
            print("Resposta:", "pong" if p.ping() else "sem resposta")
        else:
            print(p.info())
    except (par_webrtc.ParErro, IndexError) as e:
        print("Nao deu:", e or "faltou o codigo")


if __name__ == "__main__":
    main(sys.argv[1:])
