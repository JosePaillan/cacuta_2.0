@echo off
cd /d "%~dp0"

set VENV=.\.env\Scripts\activate.bat

start cmd /k "call %VENV% && cd Api_flask\sucursal_1 && python server.py"
start cmd /k "call %VENV% && cd Api_flask\sucursal_2 && python server.py"
start cmd /k "call %VENV% && cd Api_flask\sucursal_3 && python server.py"

echo Servidores iniciados en puertos 50052, 50053 y 50054
pause
