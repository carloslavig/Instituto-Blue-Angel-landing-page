# -*- coding: utf-8 -*-
"""Leitura do WhatsApp Web no Chrome da loja (porta de depuracao). So le; nao envia nada."""
import json
import re
import time
import http.client
import itertools
import websocket

_ids = itertools.count(1)

JS_LISTA = r"""
(function(){
  var out=[];
  document.querySelectorAll('#pane-side [role="row"], #pane-side [role="listitem"]').forEach(function(r){
    var t=r.querySelector('span[title]'); if(!t) return;
    out.push({nome:t.getAttribute('title'), sig:(r.innerText||'').replace(/\s+/g,' ').trim()});
  });
  return JSON.stringify(out);
})()
"""

JS_RECT = r"""(function(nome){var rows=document.querySelectorAll('#pane-side [role="row"], #pane-side [role="listitem"]');
 for(var r of rows){var t=r.querySelector('span[title]'); if(t&&t.getAttribute('title')===nome){r.scrollIntoView({block:'nearest'}); var b=r.getBoundingClientRect(); return JSON.stringify({x:b.x+b.width/2,y:b.y+b.height/2});}} return null;})(%s)"""

# O WhatsApp Web atual nao marca mais as bolhas com classes message-in/message-out: a direcao vem da POSICAO da bolha
# (enviadas ficam encostadas na direita, recebidas na esquerda).
JS_DIR = r"""function(el){var m=document.querySelector('#main'); if(!m) return 'ELE'; var a=m.getBoundingClientRect(), r=el.getBoundingClientRect();
  return (a.right-r.right) < (r.left-a.left) ? 'EU' : 'ELE';}"""

JS_MSGS = r"""
(function(max){
  var dir=""" + JS_DIR + r""";
  var msgs=[];
  document.querySelectorAll('#main [data-pre-plain-text]').forEach(function(el){
    var cab=el.getAttribute('data-pre-plain-text')||'';
    var corpo=el.querySelector('span.selectable-text, span[dir]');
    var txt=(corpo?corpo.innerText:el.innerText)||'';
    msgs.push({c:cab.replace(/\s+/g,' ').trim(), t:txt.trim(), d:dir(el)});
  });
  return JSON.stringify(msgs.slice(-max));
})(%d)
"""

JS_CONTA_ENVIADAS = r"""(function(){var dir=""" + JS_DIR + r""";
  return [].slice.call(document.querySelectorAll('#main [data-pre-plain-text]')).filter(function(e){return dir(e)==='EU'}).length;})()"""
JS_CAIXA = ("(function(){var b=document.querySelector('footer [contenteditable=\"true\"], [contenteditable=\"true\"][data-tab=\"10\"]');"
            " if(!b) return false; b.focus(); return true})()")


class Indisponivel(RuntimeError):
    pass


class WA:
    def __init__(self, porta=9223, host="127.0.0.1"):
        self.porta, self.host = porta, host

    def _url_aba(self):
        try:
            c = http.client.HTTPConnection(self.host, self.porta, timeout=5)
            c.request("GET", "/json")
            abas = json.loads(c.getresponse().read())
            c.close()
        except OSError as e:
            raise Indisponivel("Chrome da loja nao esta aberto (use ABRIR-WHATSAPP)") from e
        for a in abas:
            if a.get("type") == "page" and "web.whatsapp.com" in a.get("url", ""):
                return a["webSocketDebuggerUrl"]
        raise Indisponivel("aba do WhatsApp Web nao encontrada")

    def __enter__(self):
        self.url = self._url_aba()
        self.ws = websocket.create_connection(self.url, timeout=20, suppress_origin=True, max_size=16 * 1024 * 1024)
        self._preparar_pagina()
        return self

    def _preparar_pagina(self):
        """Janela minimizada ou aba atras de outra = pagina 'hidden' (cliques falham); lista rolada para baixo ou com texto na busca
        esconde as conversas novas (ficam no topo). Deixa tudo no estado normal. Nunca impede o uso."""
        try:
            r = self.cmd("Browser.getWindowForTarget")
            if (r.get("bounds") or {}).get("windowState") == "minimized":
                self.cmd("Browser.setWindowBounds", {"windowId": r["windowId"], "bounds": {"windowState": "normal"}})
            self.cmd("Target.activateTarget", {"targetId": self.url.rstrip("/").split("/")[-1]})
            self.cmd("Page.bringToFront")
            self.js("""(function(){var i=document.querySelector('#side input');
              if(i && i.value){i.focus(); document.execCommand('selectAll'); document.execCommand('delete'); i.blur();}
              var p=document.querySelector('#pane-side'); if(p) p.scrollTop=0;})()""")
        except Exception:
            pass

    def __exit__(self, *a):
        try:
            self.ws.close()
        except Exception:
            pass

    def cmd(self, metodo, params=None):
        mid = next(_ids)
        self.ws.send(json.dumps({"id": mid, "method": metodo, "params": params or {}}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == mid:
                if "error" in m:
                    raise RuntimeError(f"{metodo}: {m['error']}")
                return m.get("result", {})

    def js(self, expr):
        r = self.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        if r.get("exceptionDetails"):
            raise RuntimeError(str(r["exceptionDetails"])[:300])
        return r.get("result", {}).get("value")

    def logado(self):
        return bool(self.js("!!document.querySelector('#pane-side')"))

    def lista(self):
        return json.loads(self.js(JS_LISTA) or "[]")

    def abrir(self, nome):
        rc = self.js(JS_RECT % json.dumps(nome))
        if not rc:
            return False
        rc = json.loads(rc)
        self.cmd("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": rc["x"], "y": rc["y"]})
        time.sleep(0.3)
        for tipo, bt in (("mousePressed", 1), ("mouseReleased", 0)):
            self.cmd("Input.dispatchMouseEvent", {"type": tipo, "x": rc["x"], "y": rc["y"], "button": "left", "buttons": bt, "clickCount": 1})
        time.sleep(1.5)
        base = re.split(r"[^\w\s.\-]", nome)[0].strip() or nome   # emoji vira imagem no cabecalho
        chave = json.dumps(base[:12])
        return bool(self.js("[...document.querySelectorAll('header')].some(h=>h.innerText.indexOf(%s)>=0 && h.closest('#pane-side')==null && !h.closest('#side'))" % chave))

    def mensagens(self, max_msgs=15):
        return json.loads(self.js(JS_MSGS % max_msgs) or "[]")

    def enviar(self, nome, texto):
        """Abre a conversa (conferindo o cabecalho) e envia o texto. Devolve (ok, motivo). Texto em uma linha so."""
        texto = " ".join((texto or "").split())
        if not texto:
            return False, "texto vazio"
        if not self.abrir(nome):
            return False, "nao consegui abrir a conversa"
        time.sleep(0.8)
        antes = int(self.js(JS_CONTA_ENVIADAS) or 0)
        if not self.js(JS_CAIXA):
            return False, "caixa de mensagem nao encontrada"
        self.cmd("Input.insertText", {"text": texto})
        time.sleep(0.5)
        for tipo in ("keyDown", "keyUp"):
            self.cmd("Input.dispatchKeyEvent", {"type": tipo, "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13,
                                                "nativeVirtualKeyCode": 13, "text": chr(13) if tipo == "keyDown" else ""})
        for _ in range(8):
            time.sleep(0.6)
            if int(self.js(JS_CONTA_ENVIADAS) or 0) > antes:
                return True, ""
        return False, "a mensagem nao apareceu como enviada"
