# Prompt: coletar o estado do Braniac Loja / Layla (cole no Claude Code, na pasta do Braniac Loja)

Objetivo: o Carlos vai ligar o Braniac dele ao Braniac Loja (elo P2P, `par_webrtc`) e precisa saber **exatamente em que versao do codigo a Layla esta rodando nesta loja**, para o codigo novo ficar compativel. Esta tarefa e SO LEITURA: nao edite, nao instale, nao apague, nao reinicie nada.

## Cole isto no Claude Code (na pasta onde estao `loja/`, `config.ini`, `LIGAR.bat`)

```
Faca um levantamento SOMENTE LEITURA do Braniac Loja nesta pasta e me devolva UM unico relatorio em Markdown, no formato abaixo.
NAO inclua nunca: chaves de API, tokens, senhas, o conteudo de dados/chaves.json, o codigo de pareamento de par.json, numeros de telefone, nomes/enderecos de clientes, conteudo de conversas ou de estado.json. Se algum comando mostrar isso, mascare com ***.

1. VERSAO E AMBIENTE
   - Caminho da pasta, versao do Python usado pelo LIGAR.bat (veja _py.bat / python_path.txt) e `python --version`.
   - Resultado de `pip list` filtrado por: aiortc, cryptography, websocket-client, pywin32, requests, aioice, av (so nome e versao).
   - Se a pasta e um repositorio git: `git log --oneline -5` e `git status --short`. Se nao for, diga "sem git" e a data de modificacao de loja/principal.py.
2. ARQUIVOS (loja/*.py e loja/web/painel.html): para cada um, linhas e os 12 primeiros caracteres do sha1 (`certutil -hashfile <arq> SHA1` no Windows). Liste tambem qualquer arquivo em loja/ que NAO esteja na tabela de referencia abaixo, e diga quais da tabela estao ausentes.
3. PAINEL: em loja/painel.py, qual a PORTA, todas as rotas do_GET e do_POST (so os caminhos), e como _origem_ok confere Host/Origin (copie so essa funcao).
4. LAYLA: em loja/principal.py, a funcao main() (copie inteira) e a lista de funcoes de loja/atendimento.py e loja/layla.py (so nomes e assinatura). Diga se ha fila de pedidos/estado em estado.json (so as chaves de topo, sem valores) e o que o painel mostra hoje (titulos das secoes de loja/web/painel.html).
5. ELO COM O BRANIAC DO CARLOS: existe loja/par_webrtc.py? loja/par_cli.py? dados/par.json (so diga se existe e quais chaves tem, sem valores)? principal.py chama par_webrtc?
6. CONFIG: config.ini com os nomes de secoes e chaves, valores apenas de: [loja] nome, [geral] intervalo_s, [layla] ativa/responder/feedback. Os demais valores: ***.
7. TESTES: rode `python -m pytest tests -q` (ou o que existir) e diga quantos passaram/falharam, copiando so as mensagens de falha.
8. REDE: o notebook sai para a internet normalmente? Teste `curl -I https://ntfy.sh` (so o status HTTP) — o elo usa ntfy.sh para o primeiro aperto de mao.
9. DIFERENCAS: compare os hashes do item 2 com a tabela de referencia abaixo e liste os arquivos que DIFEREM (esses sao a versao "destoante").

Tabela de referencia (versao do repositorio do Carlos em 30/10/2026 — arquivos que nao mudaram com o elo):
| arquivo | sha1 (12) |
|---|---|
| `loja/assistente.py` | `09f3d6f27664` |
| `loja/atendimento.py` | `ba97f51c33ec` |
| `loja/chaves.py` | `11cd9ed19ab2` |
| `loja/comanda.py` | `0ba4e875c777` |
| `loja/conhecimento.py` | `d1239474be61` |
| `loja/controle.py` | `f3458ef4a0e1` |
| `loja/ia.py` | `62dccdf3ef8a` |
| `loja/impressora.py` | `dd088a5b4955` |
| `loja/instalacao.py` | `32a040b186c1` |
| `loja/layla.py` | `f6ed9285f445` |
| `loja/painel.py` | `e3c425a715f8` |
| `loja/whatsapp.py` | `a10a6be815f6` |
| `loja/web/painel.html` | `7a9561c9af94` |

Devolva so o relatorio, sem sugerir mudancas.
```

## Depois
Cole o relatorio de volta no Claude do Carlos (Braniac). Com ele, os arquivos `par_webrtc.py` / `par_cli.py` e o gancho no `principal.py` sao adaptados a versao real da Layla antes de instalar na loja.

## Instalar o elo na loja (quando o Carlos mandar o codigo novo)
1. Atualizar a pasta do Braniac Loja (git pull ou copiar `loja/`), rodar `INSTALAR.bat` (instala `aiortc` e `cryptography`).
2. No Braniac do Carlos, pedir ao Jarvis: *"rede par_codigo nome loja"* (gera o codigo de 16 caracteres).
3. Na loja: duplo clique em `PAREAR-COM-CARLOS.bat`, colar o codigo (ele tambem libera o painel, so leitura).
4. Fechar e abrir `LIGAR.bat`. Em ate ~1 min o predio "Braniac Loja" aparece ao lado do predio principal na aba Escritorio do Carlos; se a loja desligar, o predio some.
