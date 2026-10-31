# -*- coding: utf-8 -*-
"""Conversa da EQUIPE com a Layla (painel). Comandos simples funcionam sem IA; o resto vai para a IA (APIs, depois a local).

Colar uma chave de API no chat configura sozinho: o programa reconhece o provedor, testa e guarda (sem repetir a chave).
"""
import re
import unicodedata

from . import chaves as _chaves, controle, ia, layla


def _n(t):
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")


AJUDA = ("Posso te ajudar com:\n• \"status\": mostra como está tudo\n• \"pausar\": eu paro de responder os clientes (continuo imprimindo os pedidos)\n"
         "• \"voltar\": volto a responder\n• \"apis\": mostra as chaves de IA\n• colar uma chave do Gemini, Groq ou OpenRouter: eu configuro\n"
         "Ou pergunte qualquer coisa sobre a loja ou sobre o programa.")


def resumo_status(ctx):
    """Texto curto do estado atual. ctx = dict com cfg, estado, vivo (compartilhados com o painel)."""
    cfg, vivo = ctx["cfg"], ctx["vivo"]
    st = ia.status(cfg["chaves"])
    ok = [n for n, e in st if e == "ok"]
    linhas = [
        "WhatsApp: " + ("conectado ✅" if vivo.get("logado") else "NÃO conectado ⚠️ (abra o WhatsApp da loja e escaneie o QR)" if vivo.get("logado") is False else "ainda verificando"),
        "Layla respondendo clientes: " + ("sim" if cfg.get("responder") else "NÃO (pausada)"),
        "Pergunta de experiência (1h depois): " + ("ligada" if cfg.get("feedback") else "desligada"),
        "IAs por chave funcionando: " + (", ".join(ok) if ok else "nenhuma" + (" (uso a IA local)" if cfg["chaves"].get("local_modelo") else " (só mensagens-padrão)")),
    ]
    if vivo.get("erro"):
        linhas.append("Último problema: " + vivo["erro"][:160])
    pedidos = sum(len(c.get("pedidos", [])) for c in ctx["estado"].d.get("conv", {}).values())
    linhas.append(f"Pedidos impressos desde que liguei: {ctx['estado'].d.get('numero', 0)} (acompanhando {pedidos} para a pergunta de experiência)")
    return "\n".join(linhas)


def resumo_apis(cfg):
    linhas = []
    for nome, e in ia.status(cfg["chaves"]):
        linhas.append(f"• {nome}: {e}")
    if cfg["chaves"].get("local_modelo"):
        linhas.append(f"• IA local ({cfg['chaves']['local_modelo']}): " + ("pronta" if ia.local_disponivel(cfg["chaves"]["local_modelo"]) else "não encontrada"))
    return "Ordem de uso (quando uma acaba, passa para a próxima):\n" + "\n".join(linhas)


def _base(ctx):
    if ctx.get("base") is None:
        from . import conhecimento
        ctx["base"] = conhecimento.abrir()
    return ctx["base"]


def _base_e_equipe(texto, t, ctx):
    """Comandos da base de conhecimento e da equipe consultada. Devolve a resposta ou None se o texto nao for um desses comandos."""
    cfg = ctx["cfg"]
    m = re.match(r"^\s*equipe\s*[:\-]?\s*(.*)$", texto, re.I | re.S)
    if m:
        nomes = [x.strip() for x in re.split(r"[,;]| e ", m.group(1)) if x.strip()]
        if nomes:
            controle.gravar_equipe(nomes)
            cfg["equipe"] = nomes
            return ("Pronto! Quando eu não souber algo, pergunto para: " + ", ".join(nomes) +
                    ". Elas precisam ter uma conversa com o WhatsApp da loja (mande um oi para cada uma uma vez) e o nome tem que aparecer na conversa.")
        atuais = cfg.get("equipe") or []
        return ("Eu consulto: " + ", ".join(atuais) + ".") if atuais else "Ainda não tenho ninguém para consultar. Diga, por exemplo: equipe Raissa, Gabi"
    m = re.match(r"^\s*(?:lembra|lembre|anota|anote|guarda|guarde)(?: que| isso:?)?\s+(.{8,})$", texto, re.I | re.S)
    if m:
        n = _base(ctx).anotar(m.group(1).strip())
        return f"Anotado na base (nº {n}). Da próxima vez que um cliente perguntar isso eu já sei. 💛"
    m = re.search(r"pre[cç]o\s+(?:da|do|de|das|dos)?\s*(.+?)\s+(?:agora\s+[eé]|passa\s+(?:a|para)|para|pra|[eé]|=)\s*(?:r\$)?\s*(\d+(?:[.,]\d{1,2})?)\s*$", texto, re.I)
    if m:
        item = _base(ctx).mudar_preco(m.group(1), float(m.group(2).replace(",", ".")))
        if item:
            return f"Pronto, {item} agora custa R$ {float(m.group(2).replace(',', '.')):.2f}".replace(".", ",", 1) + ". (O site é separado: se mudar lá também, peça ao Carlos.)"
        return "Não achei esse item com certeza (ou há mais de um parecido). Diga o nome completo, por exemplo: preço do Combo Galera para 85"
    m = re.match(r"^\s*responder\s+(\d+)\s*[:\-]\s*(.+)$", texto, re.I | re.S)
    if m:
        pergunta = _base(ctx).responder_pendente(int(m.group(1)), m.group(2))
        return (f"Guardei a resposta para «{pergunta}». Da próxima vez eu respondo sozinha.") if pergunta else "Não achei essa pergunta pendente."
    if re.fullmatch(r"\W*(perguntas|pendentes|duvidas|perguntas pendentes)\W*", t):
        pend = _base(ctx).pendentes()
        if not pend:
            return "Nenhuma pergunta pendente. Tudo que os clientes perguntaram, a base soube responder ou a equipe já respondeu."
        return "Perguntas que eu não soube responder:\n" + "\n".join(f"{p['id']}) {p['pergunta']} (de {p['cliente']}, {p['quando']})" for p in pend) + "\nPara ensinar, digite: responder 1: a resposta"
    if re.fullmatch(r"\W*(base|fatos|conhecimento)\W*", t):
        r = _base(ctx).resumo()
        return f"Minha base tem {r['fatos']} informações, {r['itens']} itens de cardápio e {r['pendentes']} pergunta(s) pendente(s)."
    return None


def responder(texto, ctx, chamar_ia=None, testador=_chaves.testar):
    """Resposta da Layla para a equipe (texto simples)."""
    cfg = ctx["cfg"]
    achadas = _chaves.adicionar(texto, cfg["chaves"], testador)
    if achadas:
        return "\n".join(achadas) + "\n(apaguei a chave da conversa, ela fica guardada só neste computador)"
    t = _n(texto)
    r = _base_e_equipe(texto, t, ctx)
    if r:
        return r
    if re.search(r"\b(pausa|pausar|parar de responder|para de responder|desliga|desligar)\b", t) and "layla" in t + " layla":
        if re.search(r"experienc|avalia|feedback", t):
            controle.gravar(feedback=False)
            cfg["feedback"] = False
            return "Pronto, parei de perguntar a experiência dos clientes. Para voltar, diga \"voltar experiência\"."
        controle.gravar(responder=False)
        cfg["responder"] = False
        return "Pronto, parei de responder os clientes. Os pedidos continuam sendo impressos. Para eu voltar, diga \"voltar\"."
    if re.search(r"\b(voltar|volta|ligar|liga|ativar|ativa|retomar)\b", t):
        if re.search(r"experienc|avalia|feedback", t):
            controle.gravar(feedback=True)
            cfg["feedback"] = True
            return "Pronto, voltei a perguntar a experiência dos clientes 1 hora depois do pedido."
        controle.gravar(responder=True)
        cfg["responder"] = True
        return "Pronto, voltei a responder os clientes. 💛"
    if re.fullmatch(r"\W*(status|situacao|como esta tudo|como estao as coisas)\W*", t):
        return resumo_status(ctx)
    if re.fullmatch(r"\W*(apis?|chaves?|ias?)\W*", t):
        return resumo_apis(cfg)
    if re.fullmatch(r"\W*(ajuda|help|menu|comandos|\?)\W*", t):
        return AJUDA
    contexto = ("Você é a Layla, assistente virtual da loja, agora conversando com as DONAS e a EQUIPE (não com um cliente). Fale de forma simpática e curta. "
                "Você tem acesso ao programa Braniac Loja: imprime comandas, responde clientes e pergunta a experiência 1h depois. "
                "Se pedirem algo que você não consegue fazer, diga com sinceridade e sugira falar com o Carlos. Nunca peça nem repita senhas.\n\n"
                "ESTADO ATUAL:\n" + resumo_status(ctx) + "\n\n" + layla.sistema(layla.carregar_cadastro()).split("CADASTRO", 1)[-1])
    msgs = [{"role": "system", "content": contexto}, {"role": "user", "content": texto[:800]}]
    resp = (chamar_ia or (lambda m: ia.completar(m, cfg["chaves"])))(msgs)
    if resp:
        return resp
    return ("Estou sem IA agora. Cole aqui uma chave do Gemini, Groq ou OpenRouter que eu configuro na hora. "
            "Enquanto isso entendo estes comandos:\n" + AJUDA)
