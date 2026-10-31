@echo off
call "%~dp0_py.bat"
cd /d "%~dp0"
set /p COD=Cole o codigo que o Carlos mandou (ex.: ABCD-EFGH-IJKL-MNOP): 
%PY% -m loja.par_cli parear %COD%
%PY% -m loja.par_cli painel sim
echo Pronto. Feche e abra o LIGAR.bat para o elo ficar ativo.
pause
