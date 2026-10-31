# -*- coding: utf-8 -*-
"""Le a mensagem de pedido (formato fixo do site) e monta a comanda para impressora termica. Sem IA."""
import re
import textwrap
import unicodedata
from datetime import datetime

PEDIDO_RE = re.compile(r"gostaria de fazer um pedido", re.I)
PRECO_RE = re.compile(r"R\$\s*([\d.]+,\d{2})")


def eh_pedido(texto):
    return bool(PEDIDO_RE.search(texto or ""))


def sem_acento(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def parse_pedido(texto):
    """Devolve {itens:[{qtd,nome,detalhe,preco}], total, taxa_a_confirmar, nome, endereco, obs, pagamento}."""
    itens, total, taxa, nome, endereco, obs, pagamento = [], "", False, "", "", "", ""
    for bruta in (texto or "").splitlines():
        l = bruta.strip()
        if not l:
            continue
        if l.startswith("•"):
            corpo = l.lstrip("• ").strip()
            preco = ""
            m = re.search(r"\s-\s*(R\$\s*[\d.]+,\d{2})\s*$", corpo)
            if m:
                preco, corpo = m.group(1).replace("R$ ", "").replace("R$", "").strip(), corpo[:m.start()].strip()
            qtd = 1
            mq = re.match(r"^(\d+)\s*x\s+(.*)$", corpo, re.I)
            if mq:
                qtd, corpo = int(mq.group(1)), mq.group(2)
            detalhe = ""
            md = re.match(r"^(.*?)\s*\((.*)\)\s*$", corpo)
            if md:
                corpo, detalhe = md.group(1).strip(), md.group(2).strip()
            itens.append({"qtd": qtd, "nome": corpo, "detalhe": detalhe, "preco": preco})
            continue
        sem = l.replace("*", "").strip()
        baixo = sem.lower()
        if baixo.startswith("total"):
            mp = PRECO_RE.search(sem)
            total = mp.group(1) if mp else ""
            taxa = "taxa" in baixo
        elif baixo.startswith("nome:"):
            nome = sem[5:].strip()
        elif baixo.startswith("endere"):
            endereco = sem.split(":", 1)[1].strip() if ":" in sem else ""
        elif baixo.startswith("obs:"):
            obs = sem[4:].strip()
        elif baixo.startswith("pagamento:"):          # preferencia escolhida no site (o pagamento em si e combinado com a equipe)
            pagamento = re.sub(r"\s*\(prefer[^)]*\)\s*$", "", sem[10:].strip())
    return {"itens": itens, "total": total, "taxa_a_confirmar": taxa, "nome": nome, "endereco": endereco, "obs": obs, "pagamento": pagamento}


def _par(esq, dir_, w):
    """Linha com texto a esquerda e valor a direita."""
    espaco = w - len(esq) - len(dir_)
    if espaco < 1:
        return esq[: max(0, w - len(dir_) - 1)] + " " + dir_
    return esq + " " * espaco + dir_


def _quebra(texto, w, indent=""):
    return textwrap.wrap(texto, w, initial_indent=indent, subsequent_indent=indent) or [""]


def montar_linhas(ped, loja, numero, quando, origem="WhatsApp", contato="", w=32):
    """Lista de (tipo, texto). tipo: 'g' titulo grande centralizado, 'c' centralizado, 'n' normal, 'b' negrito."""
    L = []
    barra = "=" * w
    L.append(("c", barra))
    L.append(("g", loja.upper()))
    L.append(("g", f"PEDIDO #{numero:04d}"))
    L.append(("c", f"{quando:%d/%m/%Y  %H:%M}"))
    L.append(("c", f"via {origem}"))
    L.append(("c", barra))
    if ped["nome"]:
        for x in _quebra("CLIENTE: " + ped["nome"], w):
            L.append(("b", x))
    if contato:
        for x in _quebra("WHATSAPP: " + contato, w):
            L.append(("n", x))
    if ped["endereco"]:
        for x in _quebra("ENDERECO: " + ped["endereco"], w):
            L.append(("b", x))
    L.append(("n", "-" * w))
    for it in ped["itens"]:
        esq = f"{it['qtd']}x {it['nome']}"
        if len(esq) + len(it["preco"]) + 1 <= w:
            L.append(("b", _par(esq, it["preco"], w)))
        else:
            for x in _quebra(esq, w):
                L.append(("b", x))
            if it["preco"]:
                L.append(("n", _par("", it["preco"], w)))
        if it["detalhe"]:
            for x in _quebra(it["detalhe"], w - 3, "   "):
                L.append(("n", x))
    L.append(("n", "-" * w))
    if ped["total"]:
        L.append(("g", f"TOTAL R$ {ped['total']}"))
    if ped["taxa_a_confirmar"]:
        L.append(("c", "+ taxa de entrega (a confirmar)"))
    if ped.get("pagamento"):
        for x in _quebra("PAGAMENTO: " + ped["pagamento"] + " (preferencia)", w):
            L.append(("b", x))
    if ped["obs"]:
        L.append(("n", "-" * w))
        for x in _quebra("OBS: " + ped["obs"], w):
            L.append(("b", x))
    L.append(("c", barra))
    return L


def comanda_texto(linhas):
    return "\n".join(t for _, t in linhas) + "\n"


def comanda_bruta(texto, loja, numero, quando, w=32):
    """Mensagem que nao segue o formato do site: imprime o texto inteiro, bem legivel."""
    barra = "=" * w
    L = [("c", barra), ("g", loja.upper()), ("g", f"PEDIDO #{numero:04d}"), ("c", f"{quando:%d/%m/%Y  %H:%M}"),
         ("c", "mensagem do cliente (confira)"), ("c", barra)]
    for p in (texto or "").splitlines():
        for x in _quebra(p, w):
            L.append(("n", x))
    L.append(("c", barra))
    return L


def escpos(linhas, acentos=False, cortar=True):
    """Bytes ESC/POS (RAW). acentos=False remove acentos (mais seguro em impressoras sem a pagina de codigo PT-BR)."""
    b = bytearray(b"\x1b@")
    if acentos:
        b += b"\x1bt\x03"  # pagina PC860 (portugues)
    for tipo, txt in linhas:
        t = txt if acentos else sem_acento(txt)
        b += b"\x1ba" + (b"\x01" if tipo in ("g", "c") else b"\x00")
        b += b"\x1bE" + (b"\x01" if tipo in ("g", "b") else b"\x00")
        b += b"\x1d!" + (b"\x11" if tipo == "g" else b"\x00")
        b += t.encode("cp860" if acentos else "ascii", errors="replace") + b"\n"
    b += b"\x1d!\x00\x1bE\x00\x1ba\x00" + b"\n\n\n\n"
    if cortar:
        b += b"\x1dVB\x00"
    return bytes(b)


def agora():
    return datetime.now()
