# -*- coding: utf-8 -*-
"""Instala o elo P2P no Braniac Loja JA EM USO, sem trocar nenhum arquivo da Layla: copia par_webrtc.py/par_cli.py para loja/ e acrescenta
um bloco em loja/principal.py logo depois de 'srv_quadro = quadro_web.iniciar(ctx)'. Faz copia (.bak_antes_elo) e e seguro rodar de novo."""
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI.parent
ANCORA = "    srv_quadro = quadro_web.iniciar(ctx)\n"
BLOCO = '''    try:    # elo com o Braniac do Carlos (par_webrtc): ouve sempre; so mostra o painel depois de pareado e liberado (PAREAR-COM-CARLOS.bat)
        from . import par_webrtc
        par_webrtc.Par(RAIZ / "dados", "loja", lambda de, t: "Aqui e o Braniac Loja (Layla). Por aqui so confirmo que estou no ar.",
                       f"http://127.0.0.1:{painel.PORTA}").iniciar()
    except Exception as e:
        log(f"elo com o Braniac do Carlos nao iniciou (rode APLICAR-ELO.bat): {e!r}")
'''


def main():
    pr = RAIZ / "loja" / "principal.py"
    if not pr.exists():
        return print("Nao achei loja/principal.py em", RAIZ, "- rode: python aplicar.py CAMINHO_DA_PASTA")
    for f in ("par_webrtc.py", "par_cli.py", "elo_jarvis.py"):
        shutil.copy2(AQUI / f, RAIZ / "loja" / f)
    s = pr.read_text(encoding="utf-8")
    if "par_webrtc" in s:
        return print("principal.py ja tem o elo. Arquivos par_webrtc/par_cli atualizados.")
    if s.count(ANCORA) != 1:
        return print("Nao achei o ponto de encaixe em principal.py (versao diferente). Nada foi alterado em principal.py; mande este aviso ao Carlos.")
    shutil.copy2(pr, pr.with_name("principal.py.bak_antes_elo"))
    pr.write_text(s.replace(ANCORA, ANCORA + BLOCO, 1), encoding="utf-8")
    compile(pr.read_text(encoding="utf-8"), str(pr), "exec")
    print("Elo instalado. Feche e abra o LIGAR.bat, depois rode PAREAR-COM-CARLOS.bat.")


main()
