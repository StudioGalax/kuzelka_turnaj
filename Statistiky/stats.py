import streamlit as st
import pandas as pd
import json
import os

# Definice cest
DATA_FOLDER = 'Historie_turnaju_json'
HRACI_FILE = 'Statistiky/hraci.csv'

def zebra_style(row):
    return ['background-color: #f0f2f6'] * len(row) if row.name % 2 != 0 else ['background-color: white'] * len(row)

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
    
    # Příprava tabulky k zobrazení
    df_to_show = df_final.drop(columns=['ID'])
    df_to_show = df_to_show.sort_values(by='Body', ascending=False).reset_index(drop=True)
    df_to_show.insert(0, 'Pořadí', range(1, len(df_to_show) + 1))

    # Převedení na text pro vynucení zarovnání
    df_display = df_to_show.copy()
    df_display['Pořadí'] = df_display['Pořadí'].astype(str)
    df_display['Body'] = df_display['Body'].astype(str)

    # 4. Výstup
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.subheader("Celkové pořadí")
        
        # Aplikace stylu
        styled_df = df_display.style.apply(zebra_style, axis=1)
        styled_df.set_properties(**{'text-align': 'center'})
        styled_df.set_properties(subset=['Jméno'], **{'text-align': 'left'})
        
        st.dataframe(
            styled_df,
            use_container_width=False,
            hide_index=True,
            column_config={
                "Pořadí": st.column_config.TextColumn("Pořadí", width=40),
                "Jméno": st.column_config.TextColumn("Jméno", width=200),
                "Body": st.column_config.TextColumn("Body", width=80)
            }
        )
        
        st.subheader("Grafické srovnání")
        st.bar_chart(df_to_show.set_index('Jméno')['Body'])
else:
    st.info("Žádná data k zobrazení.")