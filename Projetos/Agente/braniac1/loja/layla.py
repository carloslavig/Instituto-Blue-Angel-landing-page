# -*- coding: utf-8 -*-
"""Layla: a assistente virtual da Libano Esfiharia. Conversa com os clientes no WhatsApp da loja para as meninas terem menos trabalho.

Regras que nao dependem da IA (codigo, nao prompt):
- sempre se apresenta como assistente virtual (nunca finge ser uma pessoa);
- pagamento, comprovante, pedido de atendente e reclamacao NAO passam pela IA: resposta fixa + aviso impresso para a equipe;
- nunca confirma taxa de entrega, prazo ou preco fora do cadastro (cadastro.json); na duvida passa para a equipe;
- resposta da IA que pareca dado bancario/CPF/chave e barrada.
"""
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOME = "Layla"


def carregar_cadastro(caminho=None):
    try:
        return json.loads(Path(caminho or RAIZ / "cadastro.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"loja": "Líbano Esfiharia"}


def _norm(t):
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")


PAGAMENTO = re.compile(r"\b(pix|cartao|credito|debito|pagamento|pagar|paguei|comprovante|troco|dinheiro|boleto|chave|transferencia|maquininha|maquina)\b")
RECLAMACAO = re.compile(r"(demorou|demorando|atrasou|atrasad|muito tempo|frio|fria|errad|faltou|falt[ao]|pessim|horrivel|ruim|cancel|reembols|estorn|devol|nao chegou|nunca chegou|cade meu|cade o pedido|absurdo|inaceitavel|decepcion)")
HUMANO = re.compile(r"(atendente|falar com (alguem|uma pessoa|a dona|o dono|gerente)|pessoa de verdade|humano|gerente|\bdona\b|\bdono\b)")
DADO_SENSIVEL = re.compile(r"(\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b|\b\d{11,}\b|ag[eê]ncia\s*\d|conta\s*(corrente)?\s*\d|chave pix)", re.I)


def classificar(texto):
    """Sem IA: 'pagamento' | 'humano' | 'reclamacao' | None."""
    n = _norm(texto)
    if PAGAMENTO.search(n):
        return "pagamento"
    if HUMANO.search(n):
        return "humano"
    if RECLAMACAO.search(n):
        return "reclamacao"
    return None


def primeiro_nome(nome):
    """Primeiro nome do contato, se for um nome (numero de telefone vira None)."""
    limpo = re.split(r"[^\w\s]", nome or "")[0].strip()
    if not limpo or re.search(r"\d", limpo):
        return None
    return limpo.split()[0].capitalize()


def sistema(cad, fase="atendimento", fatos=None, hoje=None):
    base = (
        f"Você é a {NOME}, assistente virtual (inteligência artificial) da {cad.get('loja', 'Líbano Esfiharia')}, uma esfiharia em "
        f"{cad.get('cidade', 'Barra do Garças')}. Você conversa com clientes no WhatsApp da loja para ajudar a equipe. "
        "Fale em português do Brasil, de forma natural, calorosa e curta (no máximo 3 frases, sem listas, sem markdown). "
        "Seja empática: se a pessoa estiver chateada ou com pressa, reconheça isso primeiro. Pode usar no máximo um emoji. "
        "Se ela perguntar, diga com sinceridade que é uma assistente virtual e que as meninas da loja acompanham tudo. "
        "REGRAS: (1) Use SOMENTE as informações da seção FATOS abaixo (consultadas na base da loja); nunca invente preço, sabor, prazo, promoção ou regra. "
        "Se a resposta NÃO estiver nos FATOS, diga que vai confirmar com as meninas e termine com [EQUIPE]. "
        "(2) Não prometa horário de chegada: diga que a equipe confirma. (3) A taxa de entrega só a equipe confirma depois da localização; "
        "você pode citar a tabela por distância como estimativa. (4) Nunca peça nem repita dados de pagamento, cartão, CPF ou chave Pix; "
        "pagamento é combinado com a equipe. (5) Para fazer pedido, o cliente monta no site " + cad.get("site", "") +
        " e envia por aqui; ou escreve o pedido, e você avisa a equipe com [EQUIPE]. (6) Não repita o que o cliente acabou de dizer.")
    fora = cad.get("indisponiveis") or []
    if fora:   # Raissa (15/10): sabores fora do ar; a Layla avisa com educacao e pede outro
        base += (" SABORES INDISPONIVEIS AGORA: " + ", ".join(fora) + ". Se o cliente pedir algum deles, diga com educacao que esse sabor "
                 "nao esta disponivel no momento e peca para escolher outro do cardapio; nunca aceite nem anote esse sabor.")
    if hoje:
        base += f" Hoje é {hoje}."
    if fatos is not None:
        base += "\n\nFATOS (base da loja)\n" + (fatos or "(nenhum fato relevante para esta conversa)")
    else:
        base += "\n\nCADASTRO\n" + "\n".join(f"{k.capitalize()}: {cad[k]}" for k in ("horario", "site", "whatsapp", "ifood", "cardapio", "combos", "entrega", "pagamento") if cad.get(k))
    if fase == "feedback":
        link = cad.get("google_avaliacao", "")
        base += ("\n\nCONTEXTO: você acabou de perguntar ao cliente como foi o pedido dele. Interprete a resposta. "
                 "Se foi elogio: agradeça de coração" + (f" e peça UMA vez, sem insistir, uma avaliação no Google: {link}" if link else "") +
                 ". Se houve problema ou frustração: peça desculpas sinceras, diga que vai passar para a equipe resolver, NÃO peça avaliação, e termine com [EQUIPE]. "
                 "Se for neutro ou curto, agradeça e encerre sem insistir.")
    return base


def montar_mensagens(cad, historico, texto, fase="atendimento", fatos=None, hoje=None):
    msgs = [{"role": "system", "content": sistema(cad, fase, fatos, hoje)}]
    for d, t in historico[-10:]:
        msgs.append({"role": "assistant" if d == "C" else "user", "content": t[:400]})
    msgs.append({"role": "user", "content": texto[:800]})
    return msgs


def fixa_pagamento(nome):
    n = primeiro_nome(nome)
    return (f"{n + ', e' if n else 'E'}ntendi! Pagamento a gente combina direto com as meninas da loja, por segurança eu não trato disso por aqui. "
            "Já avisei elas e já já uma delas te responde. 💛")


FIXA_HUMANO = "Claro! Já chamei uma das meninas da loja pra falar com você, ela te responde em breve. Obrigada pela paciência!"
FIXA_RECLAMACAO = ("Sinto muito por isso, de verdade. Já passei para as meninas da loja agora mesmo pra resolverem com você o quanto antes.")
FIXA_SEM_IA = ("Oi! Aqui é a Layla, assistente virtual da Líbano Esfiharia. Já avisei as meninas da loja e elas te respondem já já. "
               "Enquanto isso, o cardápio completo está em {site}.")


SOCIAL = re.compile(r"^\W*(oi+|ola|opa|e ai|bom dia|boa tarde|boa noite|obrigad[oa]s?|valeu|ok|blz|beleza|tudo bem|tudo bom|show|tchau|ate mais|de nada|certo|combinado|perfeito)")
FIXA_SEM_BASE = "Boa pergunta! Vou confirmar isso com as meninas da loja e já te respondo, tá? 💛"
SEM_BASE = "pergunta sem resposta na base"


def _so_conversa(texto):
    from .conhecimento import _tokens
    return not _tokens(texto) or (len(texto) < 40 and SOCIAL.search(_norm(texto)) is not None)


def responder(cad, historico, texto, ia, nome="", fase="atendimento", base=None, hoje=None):
    """-> (resposta, motivo_equipe). motivo_equipe e None quando nao precisa da equipe. ia(mensagens)->texto|None.
    Com `base` (conhecimento.Base), a Layla CONSULTA a base antes de responder; sem fato relevante nao chuta."""
    fatos = None
    if base is not None and fase == "atendimento" and classificar(texto) is None:
        fatos = base.contexto(texto)
        if not fatos and not _so_conversa(texto):
            return FIXA_SEM_BASE, SEM_BASE
    tipo = classificar(texto)
    if tipo == "pagamento":
        return fixa_pagamento(nome), "pagamento"
    if tipo == "humano":
        return FIXA_HUMANO, "pediu atendente"
    if tipo == "reclamacao":
        return FIXA_RECLAMACAO, "reclamacao"
    bruto = ia(montar_mensagens(cad, historico, texto, fase, fatos, hoje)) if ia else None
    if not bruto:
        return FIXA_SEM_IA.format(site=cad.get("site", "")), "IA indisponivel"
    equipe = "[EQUIPE]" in bruto
    resp = re.sub(r"\s*\[EQUIPE\]\s*", " ", bruto).replace("**", "*").strip()
    resp = " ".join(resp.split())[:700]
    if DADO_SENSIVEL.search(resp):
        return fixa_pagamento(nome), "resposta da IA barrada (dado sensivel)"
    link = cad.get("google_avaliacao", "")
    if link and fase == "feedback" and any(link in t for d, t in historico if d == "C" and t != texto):
        resp = resp.replace(link, "").strip()   # o pedido de avaliacao e feito uma unica vez
    return resp, (SEM_BASE if (equipe and base is not None) else ("pediu algo fora do cadastro" if equipe else None))


def confirmacao_pedido(nome, ped):
    n = primeiro_nome(nome) or primeiro_nome(ped.get("nome", ""))
    abre = f"Oi, {n}! " if n else "Oi! "
    txt = (abre + "Aqui é a Layla, assistente virtual da Líbano Esfiharia 🥙 Recebi o seu pedido e já avisei a cozinha. ")
    txt += ("Me manda sua localização pelo WhatsApp (clipe > Localização) pra eu passar pra equipe confirmar a taxa de entrega. "
            if ped.get("taxa_a_confirmar", True) else "A equipe já confirma o valor da entrega com você. ")
    if not ped.get("endereco"):
        txt += "E me diz o endereço completo, por favor. "
    return txt.strip() + " Qualquer dúvida, é só falar!"


def pergunta_experiencia(nome, ped, ia=None, cad=None):
    """Mensagem empatica 1h depois do pedido. Texto fixo (sem IA: nao gasta cota e nao inventa)."""
    n = primeiro_nome(nome) or primeiro_nome((ped or {}).get("nome", ""))
    abre = f"Oi, {n}! " if n else "Oi! "
    return (abre + "Aqui é a Layla, da Líbano Esfiharia 💛 Passando pra saber como foi o seu pedido: a esfiha chegou quentinha e do jeito que você queria? "
            "Me conta como foi a experiência, sua opinião ajuda muito a gente a melhorar!")
