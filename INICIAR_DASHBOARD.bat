@echo off
title Dante Hub - Dashboard & Claude Bridge
cd /d "%~dp0"
echo =========================================================
echo    DANTE HUB - PANEL DE INVESTIGACION Y PUENTE CLAUDE
echo =========================================================
echo.
echo Iniciando servidor en http://localhost:5050 ...
start "" http://localhost:5050
python server.py
pause
