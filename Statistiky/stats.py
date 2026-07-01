import streamlit as st
import pandas as pd
import json
import os

# Definice cest
DATA_FOLDER = 'Historie_turnaju_json'
HRACI_FILE = 'Statistiky/hraci.csv'

st.set_page_config(page_title="Kuželky - Statistiky", layout="wide")
st.title("📊 Statistiky kuželkářského turnaje")

# 1. Načtení seznamu hráčů
if not os.path.exists(HRACI_FILE):
    st.error(f"Chyba: Soubor {HRACI_FILE} nebyl nalezen!")
    st.stop()

df_hraci = pd.read_csv(HRACI_FILE)
df_hraci.columns = [c.strip() for c in df_hraci.columns]

# 2. Načtení JSON souborů
all_stats = []
if os.path.exists(DATA_FOLDER):
    json_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.json')]
    for file_name in json_files:
        with open(os.path.join(DATA_FOLDER, file_name), 'r', encoding='utf-8') as f:
            data = json.load(f)
            for team in data.get('teams', {}).values():
                for player_name, scores in team.items():
                    all_stats.append({"Jméno": player_name.strip(), "Body": sum(scores)})

# 3. Zpracování dat
if all_stats:
    df_results = pd.DataFrame(all_stats)
    df_total = df_results.groupby('Jméno')['Body'].sum().reset_index()
    
    # Propojení
    df_final = pd.merge(df_hraci, df_total, on='Jméno', how='left').fillna(0)
    df_final['Body'] = df_final['Body'].astype(int)
    
    # Příprava tabulky k zobrazení (odstraníme ID)
    df_to_show = df_final.drop(columns=['ID'])
    df_to_show = df_to_show.sort_values(by='Body', ascending=False).reset_index(drop=True)
    df_to_show.insert(0, 'Pořadí', range(1, len(df_to_show) + 1))

    # 4. Výstup v užším sloupci
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.subheader("Celkové pořadí")
        st.dataframe(
            df_to_show,
            use_container_width=False,  # Tady je ta změna – vypneme roztahování
            hide_index=True,
            column_config={
                "Pořadí": st.column_config.NumberColumn(
                    "Pořadí", 
                    width=40  # Zkusíme 40 pro maximální úsporu místa
                ),
                "Jméno": st.column_config.TextColumn(
                    "Jméno", 
                    width=200 # Fixní šířka pro jména, aby nebyla zbytečně velká
                ),
                "Body": st.column_config.NumberColumn(
                    "Body", 
                    width=60  # Fixní šířka pro body
                )
            }
        )
        
        st.subheader("Grafické srovnání")
        st.bar_chart(df_to_show.set_index('Jméno')['Body'])
else:
    st.info("Žádná data k zobrazení.")