import streamlit as st
import pandas as pd
import json
import os

# Definice cest - musí přesně odpovídat tvé struktuře na GitHubu
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
    
    if not json_files:
        st.warning("Ve složce Historie_turnaju_json nejsou žádné .json soubory.")
    else:
        for file_name in json_files:
            with open(os.path.join(DATA_FOLDER, file_name), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for team in data.get('teams', {}).values():
                    for player_name, scores in team.items():
                        all_stats.append({"Jméno": player_name.strip(), "Body": sum(scores)})
else:
    st.error(f"Chyba: Složka {DATA_FOLDER} nebyla nalezena!")
    st.stop()

# 3. Zpracování dat
if all_stats:
    df_results = pd.DataFrame(all_stats)
    df_total = df_results.groupby('Jméno')['Body'].sum().reset_index()
    
    # Propojení
    df_final = pd.merge(df_hraci, df_total, on='Jméno', how='left').fillna(0)
    df_final['Body'] = df_final['Body'].astype(int)
    
    # Seřazení a přidání pořadí
    df_final = df_final.sort_values(by='Body', ascending=False).reset_index(drop=True)
    df_final.insert(0, 'Pořadí', range(1, len(df_final) + 1))

    # 4. Výstup
# Vytvoříme 3 sloupce, využijeme jen ten prostřední (ten bude hlavní šířka)
col1, col2, col3 = st.columns([1, 6, 1]) 

with col2:
    st.subheader("Celkové pořadí")
    st.dataframe(
        df_final,
        use_container_width=True,
        hide_index=True
    )
    
    st.subheader("Grafické srovnání")
    st.bar_chart(df_final.set_index('Jméno')['Body'])

else:
    st.info("Žádná data k zobrazení.")