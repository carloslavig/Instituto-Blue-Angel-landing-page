@echo off
rem Instala o elo P2P no Braniac Loja. Copie a pasta elo-p2p para dentro da pasta do Braniac Loja e de duplo clique aqui.
cd /d "%~dp0.."
call _py.bat
%PY% -m pip install --disable-pip-version-check --quiet aiortc cryptography
%PY% elo-p2p\aplicar.py "%CD%"
copy /y "elo-p2p\PAREAR-COM-CARLOS.bat" "PAREAR-COM-CARLOS.bat" >nul
pause
