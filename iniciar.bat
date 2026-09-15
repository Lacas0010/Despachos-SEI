@echo off
title Gerador SEI - Servidor Web
cd /d "%~dp0"
echo Iniciando o Gerador SEI Web...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" iniciar_web.py
) else (
    python iniciar_web.py
)
pause
