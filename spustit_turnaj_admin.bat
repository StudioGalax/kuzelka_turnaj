@echo off
title Turnaj v kuzelkach - ADMIN
cd /d "%~dp0"
echo ==========================================
echo  Spoustim Turnaj v kuzelkach (ADMIN)
echo ==========================================
start "" "http://localhost:8501/?admin=yes"
python -m streamlit run turnaj_kuzelka.py
pause