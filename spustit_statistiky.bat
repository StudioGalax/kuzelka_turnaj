@echo off
title Statistiky kuzelky
cd /d "%~dp0"
echo ==========================================
echo  Spoustim Statistiky turnaje
echo ==========================================
python -m streamlit run Statistiky/stats.py
pause