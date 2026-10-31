# -*- coding: utf-8 -*-
"""Painel local do Braniac Loja (http://127.0.0.1:8770): status, interruptores, conversa com a Layla e registro.

So aceita conexoes deste computador (127.0.0.1) e confere Host/Origin, para nenhum site da internet conseguir mexer nele.
Servidor da biblioteca padrao do Python: nada para instalar, leve para notebook fraco.
"""
import json
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import assistente, chaves as _chaves, controle, ia

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = Path(__file__).resolve().parent / "web" / "painel.html"
PORTA = 8770


def montar_status(ctx):
    cfg, estado, vivo = ctx["cfg"], ctx["estado"], ctx["vivo"]
    pedidos = []
    for contato, c in estado.d.get("conv", {}).items():
        for p in c.get("pedidos", []):
            fb = p.get("fb") or ""
            pedidos.append({"numero": p["numero"], "cliente": p.get("nome") or contato, "hora": p["ts"][11:16],
                            "experiencia": "perguntei" if fb == "enviado" else ("" if not fb else "não perguntei"), "_ts": p["ts"]})
    pedidos.sort(key=lambda x: x["_ts"], reverse=True)
    hoje = datetime.now().strftime("%Y-%m-%d")
    n_hoje = sum(1 for p in pedidos if p["_ts"][:10] == hoje)
    for p in pedidos:
        p.pop("_ts")
    local = (cfg["chaves"].get("local_modelo") or "").strip()
    return {
        "whatsapp": vivo.get("logado"),
        "responder": bool(cfg.get("responder")), "feedback": bool(cfg.get("feedback")),
        "ia": [{"nome": n, "estado": e} for n, e in ia.status(cfg["chaves"])],
        "ia_local": local if local and ia.local_disponivel(local, 0.5) else "",
        "pedidos_impressos": estado.d.get("numero", 0),
        "pedidos_hoje": n_hoje,
        "erro": vivo.get("erro", ""),
        "base": _resumo_base(ctx),
        "equipe": {"configurada": list(cfg.get("equipe") or []), "achada": [t for t in vivo.get("equipe_achada", [])]},
        "avisos": list(reversed(estado.d.get("avisos_log", [])))[:30],
        "pedidos": pedidos[:30],
        "chaves": [{"nome": _chaves.NOMES[k], "mascara": _chaves.mascarar(v)} for k, v in cfg["chaves"].items() if k in _chaves.CAMPOS and v],
    }


def _resumo_base(ctx):
    try:
        return assistente._base(ctx).resumo()
    except Exception:
        return {"fatos": 0, "itens": 0, "pendentes": 0}


def ler_log(n=80):
    try:
        linhas = (RAIZ / "loja.log").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return linhas[-n:]


def fabricar_handler(ctx):
    class H(BaseHTTPRequestHandler):
        server_version = "BraniacLoja"

        def log_message(self, *a):
            pass

        def _origem_ok(self):
            host = (self.headers.get("Host") or "").split(":")[0]
            if host not in ("127.0.0.1", "localhost"):
                return False
            origem = self.headers.get("Origin")
            if origem and origem.split("://")[-1].split(":")[0] not in ("127.0.0.1", "localhost"):
                return False
            return True

        def _json(self, obj, codigo=200):
            corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self):
            if not self._origem_ok():
                return self._json({"erro": "acesso negado"}, 403)
            if self.path in ("/", "/index.html"):
                corpo = PAGINA.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(corpo)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(corpo)
            elif self.path.startswith("/api/status"):
                self._json(montar_status(ctx))
            elif self.path.startswith("/api/log"):
                self._json({"linhas": ler_log()})
            else:
                self._json({"erro": "nao encontrado"}, 404)

        def do_POST(self):
            try:
                n = int(self.headers.get("Content-Length") or 0)
                bruto = self.rfile.read(min(n, 20000))          # sempre le o corpo antes de responder (evita reset de conexao)
            except (ValueError, OSError):
                return self._json({"erro": "pedido invalido"}, 400)
            if not self._origem_ok() or "json" not in (self.headers.get("Content-Type") or ""):
                return self._json({"erro": "acesso negado"}, 403)
            try:
                dados = json.loads(bruto or b"{}")
            except ValueError:
                return self._json({"erro": "pedido invalido"}, 400)
            if self.path == "/api/chat":
                try:
                    resp = assistente.responder(str(dados.get("texto", ""))[:2000], ctx)
                except Exception as e:                      # o painel nunca deve cair por causa de uma conversa
                    resp = f"Tive um problema aqui ({str(e)[:80]}). Pode tentar de novo?"
                return self._json({"resposta": resp})
            if self.path == "/api/controle":
                novo = {k: bool(dados[k]) for k in ("responder", "feedback") if k in dados}
                ctx["cfg"].update(novo)
                controle.gravar(**novo)
                return self._json(montar_status(ctx))
            self._json({"erro": "nao encontrado"}, 404)

    return H


def iniciar(ctx, porta=PORTA):
    """Sobe o painel numa thread. Devolve o servidor, ou None se a porta ja estiver ocupada."""
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", porta), fabricar_handler(ctx))
    except OSError:
        return None
    threading.Thread(target=srv.serve_forever, daemon=True, name="painel").start()
    return srv
