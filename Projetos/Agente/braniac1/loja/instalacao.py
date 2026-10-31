# -*- coding: utf-8 -*-
"""Auxiliares do INSTALAR.bat (rodam com o Python recem-instalado): memoria do notebook, escolha do modelo local, config.ini.

Uso: python -m loja.instalacao ram | modelo | definir <chave> <valor>
"""
import ctypes
import re
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config.ini"


def ram_gb():
    class MEM(ctypes.Structure):
        _fields_ = [("tam", ctypes.c_ulong), ("uso", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("livre", ctypes.c_ulonglong),
                    ("pf_total", ctypes.c_ulonglong), ("pf_livre", ctypes.c_ulonglong), ("v_total", ctypes.c_ulonglong),
                    ("v_livre", ctypes.c_ulonglong), ("v_ext", ctypes.c_ulonglong)]
    m = MEM()
    m.tam = ctypes.sizeof(MEM)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.total / 1024 ** 3


def modelo_para_ram(gb):
    """Modelo local de reserva que o notebook aguenta ('' = melhor nao instalar)."""
    if gb >= 7.5:
        return "qwen2.5:1.5b"
    if gb >= 3.5:
        return "qwen2.5:0.5b"
    return ""


def definir(chave, valor, caminho=None):
    """Troca 'chave = ...' no config.ini (mantem comentarios e o resto do arquivo). Devolve True se achou a chave."""
    p = Path(caminho or CONFIG)
    txt = p.read_text(encoding="utf-8")
    novo, n = re.subn(rf"(?m)^({re.escape(chave)}\s*=).*$", lambda m: f"{m.group(1)} {valor}", txt, count=1)
    if n:
        p.write_text(novo, encoding="utf-8")
    return bool(n)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "ram":
        print(f"{ram_gb():.1f}")
    elif cmd == "modelo":
        print(modelo_para_ram(ram_gb()))
    elif cmd == "definir" and len(sys.argv) >= 4:
        sys.exit(0 if definir(sys.argv[2], sys.argv[3]) else 1)
    else:
        sys.exit(2)
