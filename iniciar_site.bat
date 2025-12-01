@echo off
title Iniciando Loja Fabiano

echo ================================
echo  ATIVANDO AMBIENTE VIRTUAL
echo ================================
cd /d "C:\Users\Fabiano\Documents\SITE FABIANO\site-fabiano"
call venv\Scripts\activate

echo ================================
echo  INICIANDO DJANGO (runserver)
echo ================================
start cmd /k "cd /d C:\Users\Fabiano\Documents\SITE FABIANO\site-fabiano && venv\Scripts\activate && python manage.py runserver"

echo ================================
echo  AGUARDANDO DJANGO SUBIR...
echo ================================
timeout /t 3 >nul

echo ================================
echo  INICIANDO CLOUDFLARE TUNNEL
echo ================================
start cmd /k "C:\cloudflared.exe --config C:\Users\Fabiano\.cloudflared\loja-fabiano.yml tunnel run loja-fabiano"

echo ================================
echo  SISTEMA INICIADO!
echo ================================
pause
