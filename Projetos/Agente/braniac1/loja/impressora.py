# -*- coding: utf-8 -*-
"""Impressao RAW (ESC/POS) pela fila do Windows. Funciona com qualquer impressora termica instalada."""
import sys


class ImpressoraIndisponivel(RuntimeError):
    pass


def _win32print():
    try:
        import win32print
        return win32print
    except ImportError as e:
        raise ImpressoraIndisponivel("pywin32 nao instalado (rode INSTALAR.bat)") from e


def listar():
    wp = _win32print()
    flags = wp.PRINTER_ENUM_LOCAL | wp.PRINTER_ENUM_CONNECTIONS
    return [p[2] for p in wp.EnumPrinters(flags)]


def padrao():
    return _win32print().GetDefaultPrinter()


def imprimir(dados, nome=""):
    """Envia bytes crus para a impressora. nome vazio = impressora padrao do Windows."""
    wp = _win32print()
    alvo = nome or wp.GetDefaultPrinter()
    try:
        h = wp.OpenPrinter(alvo)
    except Exception as e:
        raise ImpressoraIndisponivel(f"nao consegui abrir a impressora '{alvo}': {e}") from e
    try:
        wp.StartDocPrinter(h, 1, ("Comanda", None, "RAW"))
        try:
            wp.StartPagePrinter(h)
            wp.WritePrinter(h, dados)
            wp.EndPagePrinter(h)
        finally:
            wp.EndDocPrinter(h)
    finally:
        wp.ClosePrinter(h)
    return alvo


def escolher(config_path="config.ini"):
    """Lista as impressoras e grava a escolhida no config.ini."""
    import configparser
    nomes = listar()
    if not nomes:
        print("Nenhuma impressora encontrada. Instale o driver da impressora termica primeiro.")
        return 1
    print("Impressoras instaladas:\n")
    for i, n in enumerate(nomes, 1):
        print(f"  {i}) {n}")
    esc = input("\nDigite o numero da impressora de comandas: ").strip()
    if not esc.isdigit() or not (1 <= int(esc) <= len(nomes)):
        print("Opcao invalida.")
        return 1
    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding="utf-8")
    cfg.setdefault("impressora", {})["nome"] = nomes[int(esc) - 1]
    with open(config_path, "w", encoding="utf-8") as f:
        cfg.write(f)
    print(f"\nPronto! Impressora: {nomes[int(esc) - 1]}")
    return 0


if __name__ == "__main__":
    sys.exit(escolher() if len(sys.argv) > 1 and sys.argv[1] == "escolher" else print("\n".join(listar())) or 0)
