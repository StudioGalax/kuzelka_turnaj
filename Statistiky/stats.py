import streamlit as st
import pandas as pd
import json
import os

DATA_FOLDER = 'Historie_turnaju_json'
HRACI_FILE = 'Statistiky/hraci.csv'

st.set_page_config(page_title="Kuželky - Statistiky", layout="wide")
st.title("📊 Statistiky kuželkářského turnaje")

if not os.path.exists(HRACI_FILE):
    st.error(f"Soubor {HRACI_FILE} nenalezen!")
    st.stop()

df_hraci = pd.read_csv(HRACI_FILE)
df_hraci.columns = [c.strip() for c in df_hraci.columns]

all_stats = []
if os.path.exists(DATA_FOLDER):
    json_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.json')]
    for file_name in json_files:
        with open(os.path.join(DATA_FOLDER, file_name), 'r', encoding='utf-8') as f:
            data = json.load(f)
            for team in data.get('teams', {}).values():
                for player_name, scores in team.items():
                    all_stats.append({"Jméno": player_name.strip(), "Body": sum(scores)})

if all_stats:
    df_results = pd.DataFrame(all_stats)
    df_total = df_results.groupby('Jméno')['Body'].sum().reset_index()
    df_final = pd.merge(df_hraci, df_total, on='Jméno', how='left').fillna(0)
    df_final['Body'] = df_final['Body'].astype(int)
    df_final = df_final.sort_values(by='Body', ascending=False).reset_index(drop=True)
    df_final.insert(0, 'Pořadí', range(1, len(df_final) + 1))

    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.dataframe(df_final, hide_index=True, use_container_width=True)
        st.bar_chart(df_final.set_index('Jméno')['Body'])
else:
    st.info("Žádná data k zobrazení.")