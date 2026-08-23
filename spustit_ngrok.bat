@echo off
title Ngrok Tunel (Port 8501)
cd /d "%~dp0"
echo ==========================================
echo  Spoustim Ngrok pro zpristupneni hracum
echo  Port: 8501
echo ==========================================
echo.
echo Nech toto okno otevrene po celou dobu turnaje!
echo.
"%~dp0ngrok.exe" http 8501
pause

