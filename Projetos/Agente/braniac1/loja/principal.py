# -*- coding: utf-8 -*-
"""Laco principal do Braniac Loja (fase 1): ve pedidos novos no WhatsApp da loja e imprime a comanda."""
import configparser
import hashlib
import json
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from . import atendimento, chaves, comanda, conhecimento, controle, ia, impressora, layla, painel
from .atendimento import hora_da_mensagem
from .whatsapp import WA, Indisponivel

RAIZ = Path(__file__).resolve().parent.parent


def ler_config(caminho=None):
    cfg = configparser.ConfigParser()
    cfg.read(caminho or RAIZ / "config.ini", encoding="utf-8")
    g = lambda s, k, d: cfg.get(s, k, fallback=d)
    cfg_final = {
        "loja": g("loja", "nome", "Libano Esfiharia"),
        "intervalo": int(g("geral", "intervalo_s", "15")),
        "retroativo_min": int(g("geral", "retroativo_min", "60")),
        "porta": int(g("chrome", "porta", "9223")),
        "impressora": g("impressora", "nome", ""),
        "largura": int(g("impressora", "largura", "32")),
        "acentos": g("impressora", "acentos", "nao").lower() in ("sim", "s", "1", "true"),
        "cortar": g("impressora", "cortar", "sim").lower() in ("sim", "s", "1", "true"),
        "copias": max(1, int(g("impressora", "copias", "1"))),
        "layla": g("layla", "ativa", "sim").lower() in ("sim", "s", "1", "true"),
        "responder": g("layla", "responder", "sim").lower() in ("sim", "s", "1", "true"),
        "feedback": g("layla", "feedback", "sim").lower() in ("sim", "s", "1", "true"),
        "feedback_min": int(g("layla", "feedback_min", "60")),
        "chaves": {k: g("ia", k, "").strip() for k in ("gemini", "gemini2", "groq", "openrouter")},
    }
    cfg_final["chaves"]["local_modelo"] = g("ia", "local_modelo", "").strip()
    for k, v in chaves.carregar().items():      # chaves coladas no painel (dados/chaves.json) valem mais que o config.ini
        if v:
            cfg_final["chaves"][k] = v
    cfg_final.update(controle.ler())            # liga/desliga feito no painel
    cfg_final["equipe"] = controle.ler_equipe() or [x.strip() for x in g("equipe", "contatos", "").split(",") if x.strip()]
    return cfg_final


def log(txt):
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {txt}"
    print(linha, flush=True)
    try:
        with (RAIZ / "loja.log").open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


class Estado:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        try:
            self.d = json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.d = {}
        self.d.setdefault("numero", 0)
        self.d.setdefault("pedidos", {})      # hash -> {"numero":n,"impresso":bool}
        self.d.setdefault("iniciado", datetime.now().isoformat())

    def salvar(self):
        self.caminho.write_text(json.dumps(self.d, ensure_ascii=False), encoding="utf-8")

    def proximo(self):
        self.d["numero"] += 1
        return self.d["numero"]


def processar_mensagens(msgs, contato, estado, cfg, imprimir=None, pasta=None, ao_imprimir=None):
    """Imprime os pedidos novos. Devolve quantos foram impressos agora. ao_imprimir(ped, numero, quando) roda apos cada impressao."""
    imprimir = imprimir or impressora.imprimir          # buscado na hora (nao fixado na importacao): facil de trocar nos testes
    pasta = Path(pasta or RAIZ / "comandas")
    pasta.mkdir(exist_ok=True)
    limite = datetime.fromisoformat(estado.d["iniciado"]) - timedelta(minutes=cfg["retroativo_min"])
    feitos = 0
    for m in msgs:
        if not comanda.eh_pedido(m["t"]):
            continue
        quando, autor = hora_da_mensagem(m["c"])
        if quando and quando < limite:
            continue                                   # pedido antigo, de antes de ligar o programa
        h = hashlib.sha1((contato + "|" + m["c"] + "|" + m["t"]).encode("utf-8")).hexdigest()[:16]
        reg = estado.d["pedidos"].get(h)
        if reg and reg.get("impresso"):
            continue
        if not reg:
            reg = {"numero": estado.proximo(), "impresso": False}
            estado.d["pedidos"][h] = reg
        ped = comanda.parse_pedido(m["t"])
        quando = quando or datetime.now()
        if ped["itens"]:
            linhas = comanda.montar_linhas(ped, cfg["loja"], reg["numero"], quando, contato=contato, w=cfg["largura"])
        else:
            linhas = comanda.comanda_bruta(m["t"], cfg["loja"], reg["numero"], quando, w=cfg["largura"])
        arq = pasta / f"{quando:%Y-%m-%d_%H%M}_{reg['numero']:04d}.txt"
        arq.write_text(comanda.comanda_texto(linhas), encoding="utf-8")
        try:
            dados = comanda.escpos(linhas, cfg["acentos"], cfg["cortar"])
            for _ in range(cfg["copias"]):
                alvo = imprimir(dados, cfg["impressora"])
            reg["impresso"] = True
            feitos += 1
            log(f"IMPRESSO pedido #{reg['numero']:04d} ({contato}) em '{alvo}'")
            if ao_imprimir:
                ao_imprimir(ped, reg["numero"], quando)
        except Exception as e:                         # impressora desligada/sem papel: tenta de novo no proximo ciclo
            log(f"FALHA ao imprimir pedido #{reg['numero']:04d} ({contato}): {e} (tento de novo; copia em {arq.name})")
        estado.salvar()
    return feitos


def avisar_equipe(estado, cfg, contato, motivo, texto, imprimir=None, agora=None):
    """Imprime um aviso curto para a equipe atender na mao (no maximo 1 por conversa e motivo a cada 10 min)."""
    agora = agora or datetime.now()
    imprimir = imprimir or impressora.imprimir
    c = atendimento.conv(estado, contato)
    if agora.timestamp() - c["avisos"].get(motivo, 0) < 600:
        return
    c["avisos"][motivo] = agora.timestamp()
    log(f"AVISO EQUIPE ({contato}): {motivo} | {texto[:80]!r}")
    estado.d.setdefault("avisos_log", []).append({"quando": f"{agora:%H:%M}", "cliente": contato, "motivo": motivo})
    del estado.d["avisos_log"][:-60]
    try:
        linhas = atendimento.aviso_linhas(cfg["loja"], contato, motivo, texto, agora, cfg["largura"])
        imprimir(comanda.escpos(linhas, cfg["acentos"], cfg["cortar"]), cfg["impressora"])
    except Exception as e:
        log(f"FALHA ao imprimir aviso ({contato}): {e}")


def ciclo(w, estado, cfg, vistos, vivo=None):
    vivo = vivo if vivo is not None else {}
    vivo["logado"] = bool(w.logado())
    if not vivo["logado"]:
        vivo["erro"] = "WhatsApp Web nao esta aberto/logado no Chrome da loja"
        log("WhatsApp Web nao esta logado/carregado (escaneie o QR no Chrome da loja)")
        return
    cad = layla.carregar_cadastro()
    base = conhecimento.abrir(cadastro=cad)           # a Layla consulta esta base antes de responder qualquer cliente
    # clientes: SO IAs por chave. O modelo local pequeno erra preco/detalhe; ele atende apenas a conversa da equipe no painel
    chamar_ia = lambda msgs: ia.completar(msgs, {k: v for k, v in cfg["chaves"].items() if k != "local_modelo"})
    avisar = lambda nome, motivo, texto: avisar_equipe(estado, cfg, nome, motivo, texto)

    def enviar(nome, texto):
        time.sleep(random.uniform(3, 8))                 # nao responde na hora exata: parece gente e evita limite do WhatsApp
        ok, porque = w.enviar(nome, texto)
        log(("ENVIADO " if ok else "FALHA envio ") + f"({nome}): {texto[:90]!r}" + ("" if ok else f" [{porque}]"))
        return ok, porque

    lista = w.lista()
    equipe = atendimento.titulos_da_equipe(cfg.get("equipe", []), [l["nome"] for l in lista])
    consultar = (lambda contato, pergunta: atendimento.abrir_consulta(estado, contato, pergunta, equipe, enviar, datetime.now())) if equipe else None
    vivo = vivo if vivo is not None else {}
    vivo["equipe_achada"] = equipe
    total = 0
    for linha in lista[:12]:
        if vistos.get(linha["nome"]) == linha["sig"]:
            continue                                    # nada mudou nessa conversa
        if not w.abrir(linha["nome"]):
            continue                                    # tenta de novo no proximo ciclo
        nome, msgs = linha["nome"], w.mensagens()
        ao_imprimir = None
        if cfg["layla"]:
            ao_imprimir = lambda ped, numero, quando, n=nome: atendimento.confirmar_pedido(
                estado, n, ped, numero, quando, datetime.now(), cfg, enviar, avisar)
        total += processar_mensagens(msgs, nome, estado, cfg, ao_imprimir=ao_imprimir)
        if cfg["layla"] and atendimento.eh_da_equipe(nome, cfg.get("equipe", [])):
            atendimento.tratar_equipe(msgs, nome, estado, datetime.now(), enviar, base)   # Raissa/Gabi respondendo uma consulta
        elif cfg["layla"]:
            atendimento.tratar_conversa(msgs, nome, estado, cfg, datetime.now(), enviar, avisar, chamar_ia, cad, base=base, consultar=consultar)
        estado.salvar()
        vistos[nome] = linha["sig"]
    if cfg["layla"]:
        atendimento.rodar_consultas(estado, datetime.now(), enviar, avisar)
        atendimento.rodar_feedback(estado, cfg, datetime.now(), enviar)
        estado.salvar()
    return total


def main():
    cfg = ler_config()
    estado = Estado(RAIZ / "estado.json")
    estado.salvar()
    vistos = {}
    vivo = {"logado": None, "erro": ""}
    ctx = {"cfg": cfg, "estado": estado, "vivo": vivo, "base": conhecimento.abrir()}
    srv = painel.iniciar(ctx)
    if srv is None:   # porta do painel ocupada = outra copia ja esta ligada: duas copias imprimiriam o mesmo pedido duas vezes
        print("O Braniac Loja ja esta ligado neste computador (feche esta janela). Abra o painel em http://127.0.0.1:%d" % painel.PORTA)
        log("segunda copia recusada: ja existe um Braniac Loja ligado")
        return
    try:    # elo com o Braniac do Carlos (par_webrtc): ouve sempre; so conversa/mostra o painel depois de pareado e liberado (PAREAR-COM-CARLOS.bat)
        from . import par_webrtc
        par_webrtc.Par(RAIZ / "dados", "loja", lambda de, t: "Aqui e o Braniac Loja (Layla). Por aqui so confirmo que estou no ar.",
                       f"http://127.0.0.1:{painel.PORTA}").iniciar()
    except Exception as e:
        log(f"elo com o Braniac do Carlos nao iniciou (instale aiortc e cryptography): {e!r}")
    tem_api = any(cfg["chaves"].get(k) for k in chaves.CAMPOS)
    log(f"Braniac Loja ligado ({cfg['loja']}). Intervalo {cfg['intervalo']}s, impressora '{cfg['impressora'] or 'padrao do Windows'}'. "
        f"Layla: {'ligada' if cfg['layla'] else 'desligada'} (responder={cfg['responder']}, experiencia={cfg['feedback']}, "
        f"IA={'por chave' if tem_api else ('local' if cfg['chaves'].get('local_modelo') else 'SEM CHAVES: so mensagens-padrao')}). "
        f"Painel: http://127.0.0.1:{painel.PORTA}")
    while True:
        try:
            with WA(cfg["porta"]) as w:
                ciclo(w, estado, cfg, vistos, vivo)
            vivo["erro"] = ""
        except Indisponivel as e:
            vivo["logado"], vivo["erro"] = False, str(e)
            log(f"aguardando: {e}")
        except Exception as e:
            vivo["erro"] = f"erro no ciclo: {e!r}"[:200]
            log(f"erro no ciclo: {e!r}")
        time.sleep(cfg["intervalo"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
