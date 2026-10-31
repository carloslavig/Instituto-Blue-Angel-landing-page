# -*- coding: utf-8 -*-
"""Base de conhecimento da esfiharia (SQLite, dados/conhecimento.db): a Layla CONSULTA aqui antes de responder qualquer cliente.

Tabelas: fatos (horario, entrega, pagamento, regras...), itens (cardapio e combos com preco e dia da semana) e sem_resposta
(perguntas que a base nao cobre: a equipe responde e a resposta vira fato). A base e criada na 1a vez a partir do cadastro.json.
Sem fato relevante para a pergunta a Layla NAO inventa: avisa a equipe e registra a pergunta.
"""
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ = RAIZ / "dados" / "conhecimento.db"
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]   # datetime.weekday(): segunda = 0
PARADAS = set("de da do das dos para por com sem uma uns umas que qual quais como esta estao tem tenho ter voces voce ola oii boa bom dia tarde noite "
              "quero queria gostaria saber favor pode podem e ou ai la aqui mais menos muito pra pro num nos nao sim obrigado obrigada".split())


def _fold(t):
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")


def _tokens(t):
    out = set()
    for w in re.findall(r"[a-z0-9]+", _fold(t)):
        if len(w) >= 3 and w not in PARADAS:
            out.add(w[:-1] if w.endswith("s") and len(w) > 3 else w)
    return out


FATOS_SEMENTE = [  # (categoria, titulo, palavras-chave extras) -> o texto vem do cadastro.json
    ("horario", "Horário de funcionamento", "horario hora abre aberto abrem fecha fechado funciona funcionamento quarta domingo hoje atendem"),
    ("entrega", "Entrega e taxa", "entrega entregam delivery taxa frete km distancia bairro moto motoboy localizacao endereco ponte"),
    ("pagamento", "Formas de pagamento", "pagamento pagar pix cartao dinheiro troco credito debito"),
    ("site", "Site e pedidos", "site link cardapio pedido pedir fazer encomenda como"),
    ("contato", "Contato e iFood", "whatsapp telefone numero contato ifood app"),
]


class Base:
    def __init__(self, caminho=None):
        self.caminho = Path(caminho or ARQ)

    def _con(self):
        self.caminho.parent.mkdir(exist_ok=True)
        con = sqlite3.connect(self.caminho, timeout=10)
        con.row_factory = sqlite3.Row
        con.executescript("""
            CREATE TABLE IF NOT EXISTS fatos(id INTEGER PRIMARY KEY, categoria TEXT, titulo TEXT, texto TEXT, palavras TEXT DEFAULT '', ativo INTEGER DEFAULT 1, atualizado TEXT);
            CREATE TABLE IF NOT EXISTS itens(id INTEGER PRIMARY KEY, nome TEXT, categoria TEXT, preco REAL, descricao TEXT DEFAULT '', dia INTEGER, ativo INTEGER DEFAULT 1, atualizado TEXT);
            CREATE TABLE IF NOT EXISTS sem_resposta(id INTEGER PRIMARY KEY, pergunta TEXT, cliente TEXT, quando TEXT, resolvida INTEGER DEFAULT 0);
        """)
        return con

    # ---------- criacao ----------
    def semear(self, cad):
        """Cria a base a partir do cadastro.json, so se estiver vazia."""
        con = self._con()
        try:
            if con.execute("SELECT COUNT(*) FROM fatos").fetchone()[0] or con.execute("SELECT COUNT(*) FROM itens").fetchone()[0]:
                return False
            agora = datetime.now().isoformat(timespec="seconds")
            textos = {"horario": f"Funcionamos {cad.get('horario', '')}.", "entrega": cad.get("entrega", ""),
                      "pagamento": cad.get("pagamento") or "O pagamento é combinado com a equipe da loja depois que o pedido é confirmado; a Layla não trata de pagamento.",
                      "site": f"O cliente monta o pedido no site {cad.get('site', '')} e envia por aqui no WhatsApp, ou escreve o pedido direto na conversa.",
                      "contato": f"WhatsApp {cad.get('whatsapp', '')}. {cad.get('ifood', '')}."}
            for cat, titulo, palavras in FATOS_SEMENTE:
                con.execute("INSERT INTO fatos(categoria,titulo,texto,palavras,atualizado) VALUES(?,?,?,?,?)", (cat, titulo, textos[cat], palavras, agora))
            for nome, cat, preco, desc, dia in ITENS_SEMENTE:
                con.execute("INSERT INTO itens(nome,categoria,preco,descricao,dia,atualizado) VALUES(?,?,?,?,?,?)", (nome, cat, preco, desc, dia, agora))
            con.commit()
            return True
        finally:
            con.close()

    # ---------- consulta ----------
    def buscar(self, pergunta, limite_fatos=4, limite_itens=12):
        """(fatos, itens) relevantes para a pergunta. Listas vazias = a base nao cobre isso."""
        q = _tokens(pergunta)
        if not q:
            return [], []
        con = self._con()
        try:
            fatos = []
            for f in con.execute("SELECT * FROM fatos WHERE ativo=1"):
                forte = _tokens(f["titulo"] + " " + f["palavras"])
                score = 3 * len(q & forte) + len(q & _tokens(f["texto"]))
                if score:
                    fatos.append((score, dict(f)))
            fatos = [f for _, f in sorted(fatos, key=lambda x: -x[0])[:limite_fatos]]
            itens = []
            for i in con.execute("SELECT * FROM itens WHERE ativo=1"):
                nome_t = _tokens(i["nome"])
                score = 3 * len(q & nome_t) + 2 * len(q & _tokens(i["categoria"])) + len(q & _tokens(i["descricao"]))
                if score:
                    itens.append((score, dict(i)))
            itens = [i for _, i in sorted(itens, key=lambda x: -x[0])[:limite_itens]]
            return fatos, itens
        finally:
            con.close()

    def contexto(self, pergunta):
        """Texto com os fatos/itens relevantes para colocar no prompt ('' se a base nao cobre)."""
        fatos, itens = self.buscar(pergunta)
        linhas = [f"- {f['titulo']}: {f['texto']}" for f in fatos]
        for i in itens:
            quando = f" (só {DIAS[i['dia']]})" if i["dia"] is not None else ""
            preco = f"R$ {i['preco']:.2f}".replace(".", ",") if i["preco"] is not None else "sem preço cadastrado"
            linhas.append(f"- {i['nome']} [{i['categoria']}]{quando}: {preco}" + (f" — {i['descricao']}" if i["descricao"] else ""))
        return "\n".join(linhas)

    # ---------- edicao (pela equipe, no painel) ----------
    def anotar(self, texto, titulo=None, categoria="geral"):
        con = self._con()
        try:
            palavras = " ".join(sorted(_tokens(texto)))
            cur = con.execute("INSERT INTO fatos(categoria,titulo,texto,palavras,atualizado) VALUES(?,?,?,?,?)",
                              (categoria, (titulo or texto[:50]).strip(), texto.strip(), palavras, datetime.now().isoformat(timespec="seconds")))
            con.commit()
            return cur.lastrowid
        finally:
            con.close()

    def desativar_itens(self, nomes):
        """Marca como inativos os itens cujo nome contem algum dos nomes (sabor em falta); reativa os que sairam da lista."""
        con = self._con()
        try:
            alvos = [_fold(n) for n in nomes]
            for i in con.execute("SELECT id, nome, ativo FROM itens").fetchall():
                fora = any(a and a in _fold(i["nome"]) for a in alvos)
                if fora and i["ativo"]:
                    con.execute("UPDATE itens SET ativo=0 WHERE id=?", (i["id"],))
                elif not fora and not i["ativo"] and i["nome"].startswith("Esfiha"):
                    con.execute("UPDATE itens SET ativo=1 WHERE id=?", (i["id"],))
            con.commit()
        finally:
            con.close()

    def mudar_preco(self, nome, preco):
        """Atualiza o preco do item que melhor casa com `nome`. Devolve o nome do item, ou None se nao achou (ou se ha empate)."""
        q = _tokens(nome)
        con = self._con()
        try:
            cand = [(len(q & _tokens(i["nome"])), dict(i)) for i in con.execute("SELECT * FROM itens WHERE ativo=1")]
            cand = [c for c in cand if c[0]]
            if not cand:
                return None
            melhor = max(c[0] for c in cand)
            top = [c[1] for c in cand if c[0] == melhor]
            exato = [i for i in top if _fold(i["nome"]) == _fold(nome)]
            alvo = exato[0] if exato else (top[0] if len(top) == 1 else None)
            if not alvo:
                return None
            con.execute("UPDATE itens SET preco=?, atualizado=? WHERE id=?", (float(preco), datetime.now().isoformat(timespec="seconds"), alvo["id"]))
            con.commit()
            return alvo["nome"]
        finally:
            con.close()

    def registrar_sem_resposta(self, pergunta, cliente):
        con = self._con()
        try:
            if con.execute("SELECT 1 FROM sem_resposta WHERE resolvida=0 AND pergunta=?", (pergunta[:300],)).fetchone():
                return
            con.execute("INSERT INTO sem_resposta(pergunta,cliente,quando) VALUES(?,?,?)", (pergunta[:300], cliente[:60], datetime.now().strftime("%d/%m %H:%M")))
            con.commit()
        finally:
            con.close()

    def pendentes(self):
        con = self._con()
        try:
            return [dict(r) for r in con.execute("SELECT * FROM sem_resposta WHERE resolvida=0 ORDER BY id")]
        finally:
            con.close()

    def responder_pendente(self, numero, resposta):
        """A equipe responde uma pergunta pendente: vira fato da base e a pergunta e dada como resolvida."""
        con = self._con()
        try:
            r = con.execute("SELECT * FROM sem_resposta WHERE id=? AND resolvida=0", (numero,)).fetchone()
            if not r:
                return None
            con.execute("UPDATE sem_resposta SET resolvida=1 WHERE id=?", (numero,))
            con.commit()
        finally:
            con.close()
        self.anotar(f"Pergunta: {r['pergunta']} Resposta: {resposta.strip()}", titulo=r["pergunta"][:60], categoria="faq")
        return r["pergunta"]

    def resumo(self):
        con = self._con()
        try:
            return {"fatos": con.execute("SELECT COUNT(*) FROM fatos WHERE ativo=1").fetchone()[0],
                    "itens": con.execute("SELECT COUNT(*) FROM itens WHERE ativo=1").fetchone()[0],
                    "pendentes": con.execute("SELECT COUNT(*) FROM sem_resposta WHERE resolvida=0").fetchone()[0]}
        finally:
            con.close()

    def listar_fatos(self):
        con = self._con()
        try:
            return [dict(r) for r in con.execute("SELECT id, titulo FROM fatos WHERE ativo=1 ORDER BY id")]
        finally:
            con.close()


_SALG = ["Frango Especial", "Líbano Chefe", "Líbano", "Frango com Catupiry", "Tomate Seco c/ Rúcula", "Carne e Queijo", "Carne e Bacon", "Mussarela", "Marguerita",
         "Baiana", "Ariche", "Alemã", "Brócolis Especial", "Bacon", "Pantaneira", "Calabresa", "Quatro Queijos", "Vegetariana", "Strogonoff de Carne",
         "Strogonoff de Frango", "Carne Seca com Cream Cheese", "Frango com Cheddar"]
_DOCE = ["Brigadeiro", "Romeu e Julieta", "Chocolate com Morango", "Banoffee Real", "Chocolate com Banana", "Pequeno Sultão", "Ovomaltine", "Prestígio", "Kids", "Banana Caramelizada com Canela"]
ITENS_SEMENTE = (
    [(f"Esfiha {n}", "esfiha salgada", 12.50, "", None) for n in _SALG]
    + [(f"Esfiha {n}", "esfiha doce", 13.50, "", None) for n in _DOCE]
    + [("Coca-Cola lata", "bebida refrigerante", 6.70, "normal ou zero", None), ("Coca-Cola 1L", "bebida refrigerante", 10.90, "normal ou zero", None),
       ("Coca-Cola 1,5L", "bebida refrigerante", 12.50, "normal ou zero", None), ("Coca-Cola 2L", "bebida refrigerante", 14.00, "normal ou zero", None),
       ("Guaraná lata", "bebida refrigerante", 6.30, "normal ou zero", None), ("Guaraná 1L", "bebida refrigerante", 8.50, "normal ou zero", None),
       ("Guaraná 1,5L", "bebida refrigerante", 11.00, "normal ou zero", None), ("Guaraná 2L", "bebida refrigerante", 13.50, "normal ou zero", None)]
    + [("Combo Dupla Perfeita", "combo", 28.99, "2 esfihas (salgadas ou doces) + Guaraná lata", None),
       ("Combo Quarteto Imperdível", "combo", 55.99, "4 esfihas (salgadas ou doces) + Guaraná 1L", None),
       ("Combo Galera", "combo", 82.99, "6 esfihas (salgadas ou doces) + Coca-Cola 1L", None),
       ("Combo Banquete", "combo", 99.98, "8 esfihas (salgadas ou doces) + Guaraná 1,5L", None),
       ("Combo Festival de Esfihas", "combo", 120.99, "10 esfihas (salgadas ou doces) + Coca-Cola 1,5L", None),
       ("Combo Supremo", "combo", 146.99, "12 esfihas (salgadas ou doces) + bebida de 2L à escolha", None),
       ("Segunda em Dobro", "combo do dia", 21.90, "2 esfihas (salgadas ou doces), sem refrigerante", 0),
       ("Terça Imbatível", "combo do dia", 39.99, "3 esfihas (salgadas ou doces) + Coca-Cola lata", 1),
       ("Mega Quinta", "combo do dia", 68.90, "5 esfihas (salgadas ou doces) + Guaraná 1L + 1 esfiha doce de brinde", 3)]
)


def abrir(caminho=None, cadastro=None):
    """Base pronta para uso (cria e preenche na 1a vez)."""
    b = Base(caminho)
    from . import layla
    cad = cadastro or layla.carregar_cadastro()
    b.semear(cad)
    b.desativar_itens(cad.get("indisponiveis") or [])   # sabores fora do ar nao entram nas respostas nem nos precos
    return b


def hoje():
    return DIAS[datetime.now().weekday()]
