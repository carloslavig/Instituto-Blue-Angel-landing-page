# Prompt para o Claude da loja instalar o elo (cole no Claude Code, na pasta do Braniac Loja)

1. Copie o arquivo `elo-p2p.zip` para dentro da pasta do Braniac Loja (onde ficam `loja\`, `LIGAR.bat`) e depois cole o texto abaixo.

```
Instale o "elo P2P" no Braniac Loja desta pasta. O pacote esta em elo-p2p.zip (nesta pasta).
Regras: nao troque nenhum arquivo da Layla alem do que descrevo; nao mexa em config.ini, dados\, estado.json nem em chaves; nao reinicie a Layla sem eu confirmar (ela esta atendendo clientes).
Passos:
1. Extraia elo-p2p.zip aqui (cria a pasta elo-p2p\). Leia elo-p2p\aplicar.py e elo-p2p\par_webrtc.py e me diga em 3 linhas o que fazem (so conferir que nada manda dados para fora alem do ntfy.sh e do canal WebRTC cifrado).
2. Instale as bibliotecas com o mesmo Python do LIGAR.bat (py -3): py -3 -m pip install aiortc cryptography
3. Rode: py -3 elo-p2p\aplicar.py "<caminho desta pasta>"   (ele faz copia principal.py.bak_antes_elo e acrescenta um bloco depois de "srv_quadro = quadro_web.iniciar(ctx)").
   Se disser que nao achou o ponto de encaixe, NAO force: me mostre a funcao main() de loja\principal.py.
4. Copie elo-p2p\PAREAR-COM-CARLOS.bat para esta pasta.
5. Confira: py -3 -c "import loja.principal" sem erro, e py -3 -m loja.par_cli status mostrando pareado=False.
6. Me avise quando terminar e diga que o Carlos precisa fechar e abrir o LIGAR.bat quando a loja puder ficar 1 minuto sem atendimento. Depois eu rodo PAREAR-COM-CARLOS.bat com o codigo que o Carlos mandar.
```
