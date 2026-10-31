# Prompt para o Claude da loja: Layla fala com o Jarvis pelo elo P2P (cole no Claude Code, na pasta do Braniac Loja)

Pre-requisito: o elo ja instalado e pareado (elo-p2p.zip + PAREAR-COM-CARLOS.bat). Antes de colar, copie o `elo-p2p.zip` NOVO (tem `elo_jarvis.py`) para a pasta do Braniac Loja.

```
Objetivo: sempre que a Layla precisar falar com o Jarvis (consulta, check-in, aviso, relatorio, pergunta), ela deve tentar PRIMEIRO o canal P2P com o Braniac do Carlos e so cair no WhatsApp (como faz hoje) se o canal falhar. O Carlos registra e le a conversa do lado dele. A Layla atende clientes reais: nada pode ficar sem resposta nem duplicar mensagem.

Regras: faca copias .bak_antes_jarvis dos arquivos que editar; mudancas minimas; NAO mexa em config.ini, dados\, estado.json, chaves; NAO reinicie a Layla sem eu confirmar; NUNCA envie para o canal chaves, PIN, telefones ou nomes/enderecos de clientes (mande so o que o Jarvis precisa saber, ex.: "cliente pediu desconto de 10% no combo", "faltou massa").

Passos:
1. Extraia o elo-p2p.zip novo aqui e rode: py -3 elo-p2p\aplicar.py "<esta pasta>"  (copia par_webrtc.py, par_cli.py e elo_jarvis.py para loja\ e confere o encaixe no principal.py).
2. Leia loja\jarvis.py e todos os pontos de loja\atendimento.py / loja\principal.py que mandam mensagem ao Jarvis pelo WhatsApp (consulta, check-in, avisos, relatorios).
3. Em cada ponto de ENVIO ao Jarvis, antes de enviar pelo WhatsApp, chame:
      from . import elo_jarvis
      resp = elo_jarvis.falar(tipo, texto)      # tipo: "consulta" | "checkin" | "aviso" | "relatorio" | "pergunta"
   - Se resp for um texto: trate-o exatamente como se o Jarvis tivesse respondido no WhatsApp (mesmo caminho do codigo que le a resposta) e NAO envie pelo WhatsApp.
   - Se resp for None (canal fora): envie pelo WhatsApp como hoje, sem mudar nada.
   - Registre em loja.log uma linha curta: "JARVIS via elo (tipo)" ou "JARVIS via WhatsApp (elo fora)".
   - elo_jarvis.falar pode demorar ate ~75 s na 1a vez; nao deve travar o ciclo que atende clientes: chame-o em thread/ponto onde o atraso nao bloqueie o atendimento (como o resto do codigo ja faz para consultas).
4. Escreva um teste simples (unittest, o pytest nao esta instalado) que simule elo_jarvis.falar devolvendo texto e devolvendo None e confira os dois caminhos. Rode-o.
5. Confira: py -3 -c "import loja.principal". Nao reinicie.
6. Me devolva: arquivos alterados, os pontos onde encaixou (nome da funcao), resultado do teste e o que NAO conseguiu encaixar. Diga que o Carlos pode reiniciar o LIGAR.bat quando a loja puder ficar 1 minuto parada; depois do reinicio, mande uma mensagem de teste: py -3 -c "from loja import elo_jarvis; print(elo_jarvis.falar('teste','Layla testando o canal'))"  (deve voltar uma resposta do Jarvis).
```
