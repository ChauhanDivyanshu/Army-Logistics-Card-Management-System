@echo off
title Warehouse Operations
cd /d %~dp0

REM Start API in background
start "API" python api_server.py
timeout /t 3 /nobreak >nul

REM Start main app
python main.py
