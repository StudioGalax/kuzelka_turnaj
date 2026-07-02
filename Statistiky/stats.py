import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

# Definice cest
DATA_FOLDER = 'Historie_turnaju_json'
HRACI_FILE = 'Statistiky/hraci.csv'

# Pomocná funkce pro zebra styl
def get_styled_table(df, sort_col):
    df = df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
    df.insert(0, 'Pořadí', range(1, len(df) + 1))
        
    # Zebra styl
    def zebra_style(row):
        return ['background-color: #f0f2f6'] * len(row) if row.name % 2 != 0 else ['background-color: white'] * len(row)
        
    return df.style.apply(zebra_style, axis=1).to_html(index=False, escape=False, justify='center')

st.set_page_config(page_title="Kuželky - Statistiky", layout="wide")
st.title("📊 Statistiky kuželkářského turnaje")

# 1. Načtení dat (zůstává stejné)
if not os.path.exists(HRACI_FILE):
    st.error(f"Chyba: Soubor {HRACI_FILE} nebyl nalezen!")
    st.stop()

# 2. Načtení JSON a zpracování
all_stats = []
if os.path.exists(DATA_FOLDER):
    json_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.json')]
    for file_name in json_files:
        with open(os.path.join(DATA_FOLDER, file_name), 'r', encoding='utf-8') as f:
            data = json.load(f)
            for team in data.get('teams', {}).values():
                for player_name, scores in team.items():
                    all_stats.append({"Jméno": player_name.strip(), "Body": sum(scores)})

# 3. Zpracování dat (s novou logikou formy)
if all_stats:
    df_results = pd.DataFrame(all_stats)
    
    def get_forma(data):
        if len(data) < 3: return "➡️" 
        posledni = data[-1]
        prumer_predchozich = sum(data[-3:-1]) / 2 
        rozdil = posledni - prumer_predchozich
        if rozdil >= 10: return '<span style="color:green">⬆️</span>'
        if rozdil <= -10: return '<span style="color:red">⬇️</span>'
        return '<span style="color:blue">➡️</span>'

    hraci_data = []
    for jmeno, group in df_results.groupby('Jméno'):
        body_seznam = group['Body'].tolist()
        hraci_data.append({
            "Jméno": jmeno,
            "Celkem": sum(body_seznam),
            "Průměr": round(sum(body_seznam) / len(body_seznam), 1),
            "Forma": get_forma(body_seznam)
        })
    
    df_final = pd.DataFrame(hraci_data)
    
    # 4. Výstup v záložkách
    tab1, tab2, tab3 = st.tabs(["Celkové pořadí", "Pořadí dle průměru", "Archiv turnajů"])
    
    with tab1:
        st.subheader("Celkové pořadí")
        st.write(get_styled_table(df_final[['Jméno', 'Celkem', 'Forma']], 'Celkem'), unsafe_allow_html=True)

    with tab2:
        st.subheader("Pořadí dle průměru")
        st.write(get_styled_table(df_final[['Jméno', 'Průměr', 'Forma']], 'Průměr'), unsafe_allow_html=True)
        
    with tab3:
        st.subheader("Archiv turnajů")
        for file_name in sorted(os.listdir(DATA_FOLDER), reverse=True):
            if file_name.endswith('.json'):
                st.text(f"Turnaj: {file_name.replace('.json', '')}")
else:
    st.info("Žádná data k zobrazení.")