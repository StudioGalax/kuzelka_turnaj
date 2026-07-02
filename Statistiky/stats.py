import streamlit as st
import pandas as pd
import json
import os

# 1. NAČTENÍ DAT
# (Tady tvůj kód pro načítání zůstává, jen se ujisti, že df_final obsahuje všechny sloupce)
# ... [tvůj kód pro all_stats a df_final] ...

def display_table(df, sort_by, columns_to_show):
    # Vybereme jen ty sloupce, které skutečně máme
    existing_cols = [c for c in columns_to_show if c in df.columns]
    df_show = df[existing_cols].copy()
    
    # Seřazení
    if sort_by in df_show.columns:
        df_show = df_show.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
    
    # Přidání pořadí
    df_show.insert(0, 'Pořadí', range(1, len(df_show) + 1))
    
    # Zobrazení
    st.dataframe(
        df_show, 
        hide_index=True, 
        use_container_width=True
    )

# V hlavním bloku:
tab1, tab2 = st.tabs(["Celkové pořadí", "Pořadí dle průměru"])

with tab1:
    display_table(df_final, 'Celkem', ['Jméno', 'Celkem', 'Best kolo', 'Forma'])

with tab2:
    display_table(df_final, 'Průměr na hod', ['Jméno', 'Průměr na hod', 'Best kolo', 'Forma'])