# -*- coding: utf-8 -*-
"""Atendimento da Layla (fase 2 e 3): responde clientes, confirma pedidos impressos e pergunta a experiencia 1h depois.

Logica separada da tela/WhatsApp (tudo entra por funcoes passadas): enviar(nome, texto)->(ok, motivo), avisar(nome, motivo, texto),
ia(mensagens)->texto|None. Assim da para testar sem Chrome e sem internet.

Salvaguardas:
- se uma PESSOA da equipe escreveu na conversa (mensagem que nao foi a Layla), a Layla fica quieta nesse chat por 30 min;
- no maximo 6 respostas automaticas por conversa por hora; nunca responde grupos;
- pagamento, pedido de atendente e reclamacao viram aviso IMPRESSO para a equipe (ver layla.py);
- pergunta de experiencia: so 1h depois do pedido e so se ainda for antes da meia-noite; nunca para quem reclamou.
"""
import hashlib
import re
import time
from datetime import datetime, timedelta

from . import comanda, layla

CAB_RE = re.compile(r"\[(\d{1,2}):(\d{2}),\s*(\d{1,2})/(\d{1,2})/(\d{4})\]\s*(.*?):\s*$")
PAUSA_MIN = 30
MAX_RESP_HORA = 6
ABRE_HORA = 18          # Layla so responde cliente a partir das 18h (pedido da Raissa, 14/10)


def hora_da_mensagem(cab):
    m = CAB_RE.search(cab or "")
    if not m:
        return None, ""
    h, mi, d, mo, a, autor = m.groups()
    try:
        return datetime(int(a), int(mo), int(d), int(h), int(mi)), autor
    except ValueError:
        return None, autor


def _h(*partes):
    return hashlib.sha1("|".join(partes).encode("utf-8")).hexdigest()[:14]


def _chave_texto(t):
    return _h(re.sub(r"\W+", "", (t or "").lower()))


def conv(estado, contato):
    c = estado.d.setdefault("conv", {}).setdefault(contato, {})
    c.setdefault("hist", [])
    c.setdefault("vistos", [])
    c.setdefault("pausa_ate", 0)
    c.setdefault("resp", [])
    c.setdefault("pedidos", [])
    c.setdefault("avisos", {})
    c.setdefault("aguardando_feedback", False)
    c.setdefault("reclamou", False)
    return c


def registrar_envio(estado, contato, texto):
    """A Layla enviou: guarda no historico e lembra do texto (para nao confundir com uma pessoa da equipe)."""
    c = conv(estado, contato)
    c["hist"] = (c["hist"] + [["C", texto]])[-16:]
    minhas = estado.d.setdefault("minhas", [])
    minhas.append(_chave_texto(texto))
    del minhas[:-400]


def _registrar_entrada(c, texto):
    c["hist"] = (c["hist"] + [["E", texto]])[-16:]


def detectar_pausa_humana(msgs, c, estado, agora):
    """Mensagem ENVIADA recentemente que nao foi a Layla => uma pessoa da equipe assumiu a conversa."""
    minhas = set(estado.d.get("minhas", []))
    for m in msgs:
        if m.get("d") != "EU" or not m.get("t"):
            continue
        if _chave_texto(m["t"]) in minhas:
            continue
        quando, _ = hora_da_mensagem(m["c"])
        if quando and (agora - quando) <= timedelta(minutes=PAUSA_MIN):
            c["pausa_ate"] = max(c["pausa_ate"], (quando + timedelta(minutes=PAUSA_MIN)).timestamp())
            c["aguardando_feedback"] = False


def aviso_linhas(loja, contato, motivo, texto, quando, w=32):
    barra = "=" * w
    L = [("c", barra), ("g", "ATENCAO"), ("c", f"{quando:%d/%m  %H:%M}"), ("c", "cliente precisa de uma pessoa"), ("c", barra),
         ("b", "CLIENTE: " + contato[:w])]
    for x in comanda._quebra("MOTIVO: " + motivo, w):
        L.append(("b", x))
    if texto:
        L.append(("n", "-" * w))
        for x in comanda._quebra("Disse: " + texto[:240], w):
            L.append(("n", x))
    L.append(("c", barra))
    return L


def tratar_conversa(msgs, contato, estado, cfg, agora, enviar, avisar, ia, cad, ao_responder=None, base=None, consultar=None):
    """Responde as mensagens novas (que nao sao pedido do site) de UMA conversa. Devolve quantas respostas enviou."""
    c = conv(estado, contato)
    detectar_pausa_humana(msgs, c, estado, agora)
    limite = datetime.fromisoformat(estado.d["iniciado"]) - timedelta(minutes=cfg["retroativo_min"])
    novos = []
    for m in msgs:
        if m.get("d") != "ELE" or not m.get("t") or comanda.eh_pedido(m["t"]):
            continue
        h = _h(contato, m["c"], m["t"])
        if h in c["vistos"]:
            continue
        c["vistos"] = (c["vistos"] + [h])[-120:]
        quando, _ = hora_da_mensagem(m["c"])
        if quando and quando < limite:
            continue
        novos.append(m)
    if not novos:
        return 0
    autores = {hora_da_mensagem(m["c"])[1] for m in novos if hora_da_mensagem(m["c"])[1]}
    texto = " ".join(m["t"] for m in novos)
    _registrar_entrada(c, texto)
    if len(autores) > 1 or not cfg.get("responder", True):
        return 0                                           # grupo, ou respostas automaticas desligadas: so acompanha
    if c["pausa_ate"] > agora.timestamp():
        return 0                                           # uma pessoa da equipe esta cuidando desta conversa
    abre = int(cfg.get("abre_hora", ABRE_HORA))
    if abre <= agora.hour < 24 or agora.hour < int(cfg.get("fecha_madrugada", 0)):
        pass                                               # dentro do horario de atendimento
    else:
        # Raissa (13 e 14/10): cliente que escreve antes das 18h nao recebe resposta da Layla; a equipe e avisada
        avisar(contato, f"mensagem antes das {abre}h: nao respondi (regra da Raissa)", texto)
        return 0
    c["resp"] = [t for t in c["resp"] if agora.timestamp() - t < 3600]
    if len(c["resp"]) >= MAX_RESP_HORA:
        avisar(contato, "muitas mensagens seguidas: parei de responder sozinha", texto)
        return 0
    fase = "feedback" if c["aguardando_feedback"] else "atendimento"
    resp, motivo = layla.responder(cad, c["hist"][:-1], texto, ia, contato, fase, base=base, hoje=DIAS_SEMANA[agora.weekday()])
    if ao_responder:
        ao_responder()
    ok, porque = enviar(contato, resp)
    if ok:
        registrar_envio(estado, contato, resp)
        c["resp"].append(agora.timestamp())
        c["aguardando_feedback"] = False
    else:
        avisar(contato, f"nao consegui responder ({porque})", texto)
    if motivo:
        if "reclamacao" in motivo:
            c["reclamou"] = True
        if motivo in (layla.SEM_BASE, "pediu algo fora do cadastro"):
            if base is not None:
                base.registrar_sem_resposta(texto, contato)      # a equipe responde e a resposta entra na base
            if consultar and consultar(contato, texto):          # perguntou para a Raissa/Gabi: elas respondem pelo WhatsApp
                return 1 if ok else 0
        avisar(contato, motivo, texto)
    return 1 if ok else 0


# ---------- consulta a equipe (Raissa / Gabi) quando a base nao cobre a pergunta ----------

DIAS_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
ESPERA_AVISO_MIN = 15      # sem resposta da equipe: avisa o cliente que ainda esta confirmando e imprime aviso
ESPERA_DESISTE_MIN = 90
SEMPRE = re.compile(r"^\s*(sempre|vale (pra|para) todos)\b[\s:,\-]*", re.I)


def _n(t):
    return layla._norm(t)


def titulos_da_equipe(nomes, titulos):
    """Titulos de conversa do WhatsApp que correspondem aos nomes configurados da equipe (ex.: 'Raissa' casa com 'Miranda ✨ Raissa')."""
    alvos = [_n(x) for x in nomes if x.strip()]
    return [t for t in titulos if any(a and a in _n(t) for a in alvos)]


def eh_da_equipe(titulo, nomes):
    return bool(titulos_da_equipe(nomes, [titulo]))


def abrir_consulta(estado, contato, pergunta, equipe, enviar, agora):
    """Pergunta a Raissa/Gabi (todas as conversas em `equipe`). Devolve True se a mensagem chegou a alguem."""
    consultas = estado.d.setdefault("consultas", [])
    if any(q["cliente"] == contato and not q.get("resposta") and not q.get("encerrada") for q in consultas):
        return True                                   # ja ha uma pergunta em aberto deste cliente
    numero = (consultas[-1]["id"] + 1) if consultas else 1
    nome = layla.primeiro_nome(contato) or contato
    texto = (f"🔔 Consulta #{numero} da Layla: o cliente {nome} perguntou «{pergunta[:300]}» e eu não tenho essa informação. "
             f"Pode me responder aqui? Eu repasso para ele. (Se a resposta valer para todos os clientes, comece com \"sempre:\" que eu guardo na base.)")
    enviados = [t for t in equipe if enviar(t, texto)[0]]
    if not enviados:
        return False
    consultas.append({"id": numero, "cliente": contato, "pergunta": pergunta[:300], "quando": agora.isoformat(timespec="seconds"),
                      "consultados": enviados, "resposta": None, "avisado": False, "encerrada": False})
    del consultas[:-50]
    return True


def tratar_equipe(msgs, titulo, estado, agora, enviar, base=None):
    """Resposta da Raissa/Gabi (conversa `titulo`) a uma consulta aberta: repassa ao cliente. Devolve quantas respostas repassou."""
    c = conv(estado, titulo)
    abertas = [q for q in estado.d.get("consultas", []) if not q.get("resposta") and not q.get("encerrada") and titulo in q["consultados"]]
    repassadas = 0
    for m in msgs:
        if m.get("d") != "ELE" or not m.get("t"):
            continue
        h = _h("equipe", titulo, m["c"], m["t"])
        if h in c["vistos"]:
            continue
        c["vistos"] = (c["vistos"] + [h])[-120:]
        quando, _ = hora_da_mensagem(m["c"])
        if not abertas or (quando and quando < datetime.fromisoformat(abertas[0]["quando"]) - timedelta(minutes=1)):
            continue
        alvo = abertas[0]
        mn = re.search(r"#\s*(\d+)", m["t"])
        if mn:
            alvo = next((q for q in abertas if q["id"] == int(mn.group(1))), alvo)
        resposta = re.sub(r"#\s*\d+", "", m["t"]).strip()
        sempre = SEMPRE.match(resposta)
        resposta = SEMPRE.sub("", resposta).strip()
        if not resposta:
            continue
        nome = layla.primeiro_nome(alvo["cliente"])
        ok, _ = enviar(alvo["cliente"], (f"{nome}, " if nome else "") + "confirmei com as meninas da loja: " + resposta[:600])
        if ok:
            registrar_envio(estado, alvo["cliente"], resposta)
            alvo["resposta"] = resposta
            abertas = [q for q in abertas if q is not alvo]
            repassadas += 1
            if sempre and base is not None:
                base.anotar(f"Pergunta: {alvo['pergunta']} Resposta: {resposta}", titulo=alvo["pergunta"][:60], categoria="faq")
            enviar(titulo, f"Anotado e repassado ao cliente ✅ (consulta #{alvo['id']})" + (" Guardei na base para os próximos." if sempre and base is not None else ""))
    return repassadas


def rodar_consultas(estado, agora, enviar, avisar):
    """Consulta sem resposta: depois de 15 min avisa o cliente e a equipe (impresso); depois de 90 min desiste."""
    for q in estado.d.get("consultas", []):
        if q.get("resposta") or q.get("encerrada"):
            continue
        idade = (agora - datetime.fromisoformat(q["quando"])).total_seconds() / 60
        if idade >= ESPERA_DESISTE_MIN:
            q["encerrada"] = True
            avisar(q["cliente"], "consulta sem resposta da equipe: atender na mão", q["pergunta"])
        elif idade >= ESPERA_AVISO_MIN and not q.get("avisado"):
            q["avisado"] = True
            enviar(q["cliente"], "Ainda estou confirmando essa informação com as meninas, só mais um pouquinho, tá? 💛")
            avisar(q["cliente"], "a equipe ainda não respondeu a consulta da Layla", q["pergunta"])


def confirmar_pedido(estado, contato, ped, numero, quando, agora, cfg, enviar, avisar):
    """Pedido impresso: guarda para a pergunta de experiencia e (se permitido) confirma ao cliente. Devolve True se enviou."""
    c = conv(estado, contato)
    if not any(p["numero"] == numero for p in c["pedidos"]):
        c["pedidos"].append({"numero": numero, "ts": quando.isoformat(), "fb": None, "nome": ped.get("nome", "")})
    if not cfg.get("responder", True) or c["pausa_ate"] > agora.timestamp():
        return False
    ok, porque = enviar(contato, layla.confirmacao_pedido(contato, ped))
    if ok:
        registrar_envio(estado, contato, layla.confirmacao_pedido(contato, ped))
        c["resp"].append(agora.timestamp())
    else:
        avisar(contato, f"nao consegui confirmar o pedido ao cliente ({porque})", "")
    return ok


def rodar_feedback(estado, cfg, agora, enviar):
    """Pergunta a experiencia 1h depois do pedido, SO se ainda for antes da meia-noite do dia do pedido. Devolve quantas enviou."""
    if not cfg.get("feedback", True) or not cfg.get("responder", True):
        return 0
    enviadas = 0
    for contato, c in estado.d.get("conv", {}).items():
        for p in c.get("pedidos", []):
            if p.get("fb"):
                continue
            ts = datetime.fromisoformat(p["ts"])
            due = ts + timedelta(minutes=cfg.get("feedback_min", 60))
            if due.date() != ts.date() or agora.date() != ts.date():
                p["fb"] = "pulado: passaria da meia-noite"
                continue
            if agora < due:
                continue
            if c.get("reclamou"):
                p["fb"] = "pulado: cliente reclamou"
                continue
            if c.get("pausa_ate", 0) > agora.timestamp():
                continue                                    # a equipe esta conversando: tenta de novo no proximo ciclo
            if any(q.get("fb") == "enviado" and q.get("ts", "")[:10] == p["ts"][:10] for q in c["pedidos"]):
                p["fb"] = "pulado: ja perguntei hoje"
                continue
            texto = layla.pergunta_experiencia(contato, p)
            ok, _ = enviar(contato, texto)
            if ok:
                p["fb"] = "enviado"
                registrar_envio(estado, contato, texto)
                c["aguardando_feedback"] = True
                enviadas += 1
    return enviadas
