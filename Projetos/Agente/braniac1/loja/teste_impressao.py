# -*- coding: utf-8 -*-
"""Imprime uma comanda de exemplo para testar a impressora e a largura."""
import sys
from . import comanda, impressora
from .principal import ler_config

EXEMPLO = """Olá! Gostaria de fazer um pedido na *Líbano Esfiharia*:

• Combo Dupla Perfeita (Líbano Chefe, Prestígio) - R$ 28,99
• 2x Coca-Cola lata - R$ 13,40

*Total: R$ 42,39 + taxa de entrega conforme o endereço*
Nome: Cliente Teste
Endereço: Rua Exemplo, 123 - Bairro

Agora mande a sua localização para confirmarmos sua taxa."""


def main():
    cfg = ler_config()
    ped = comanda.parse_pedido(EXEMPLO)
    linhas = comanda.montar_linhas(ped, cfg["loja"], 0, comanda.agora(), contato="(teste)", w=cfg["largura"])
    print(comanda.comanda_texto(linhas))
    try:
        alvo = impressora.imprimir(comanda.escpos(linhas, cfg["acentos"], cfg["cortar"]), cfg["impressora"])
        print(f"Enviado para a impressora: {alvo}")
        return 0
    except Exception as e:
        print(f"NAO IMPRIMIU: {e}")
        print("Rode ESCOLHER-IMPRESSORA.bat e tente de novo.")
        return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
