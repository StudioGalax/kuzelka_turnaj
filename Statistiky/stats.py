import streamlit as st
import pandas as pd
import json
import os

# Nastavení
DATA_FOLDER = 'Historie_turnaju_json'
st.set_page_config(page_title="Kuželky - Statistiky", layout="wide")
st.title("📊 Statistiky kuželkářského turnaje")

# 1. NAČTENÍ DAT
all_stats = []
if os.path.exists(DATA_FOLDER):
    for file_name in os.listdir(DATA_FOLDER):
        if file_name.endswith('.json'):
            # Vytáhne číslo kola z názvu souboru (např. 1 z "turnaj_1.json")
            kolo = "".join([c for c in file_name if c.isdigit()])
            if not kolo: kolo = "1" # Záložní hodnota
            with open(os.path.join(DATA_FOLDER, file_name), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for team in data.get('teams', {}).values():
                    for p_name, scores in team.items():
                        all_stats.append({"Jméno": p_name.strip(), "Body": sum(scores), "Kolo": kolo})

if all_stats:
    df_raw = pd.DataFrame(all_stats)

    # 2. LOGIKA FORMY A STATISTIK
    def get_forma(body_list):
        if len(body_list) < 3: return "➡️"
        rozdil = body_list[-1] - (sum(body_list[-3:-1]) / 2)
        if rozdil >= 10: return '<span style="color:green">⬆️</span>'
        if rozdil <= -10: return '<span style="color:red">⬇️</span>'
        return '<span style="color:blue">➡️</span>'

    def process_stats(group):
        # group['Body'] obsahuje seznam náhozů (těch 50, 50, 60, 50...)
        body = group['Body'].tolist()
        
        # Najdeme index nejvyššího náhozu (idxmax vrací pozici v seznamu)
        # Protože indexy jsou 0, 1, 2, 3, přičteme 1, abychom měli 1, 2, 3, 4
        idx_max = pd.Series(body).idxmax()
        kolo_cislo = idx_max + 1 
        
        return pd.Series({
            "Celkem": sum(body),
            "Průměr": sum(body) / len(body),
            "Max v kole": f"{max(body)} ({kolo_cislo}. kolo)",
            "Forma": get_forma(body)
        })

    df_final = df_raw.groupby('Jméno').apply(process_stats).reset_index()

    # 3. VÝSTUP (TABULKY)
    def render_table(df, sort_by):
        df = df.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
        df.insert(0, 'Pořadí', range(1, len(df) + 1))
        
        if 'Průměr' in df.columns:
            df['Průměr'] = df['Průměr'].map('{:.1f}'.format)
        
        # TADY je ta změna: použijeme st.dataframe místo st.write s HTML
        # hide_index="index" skryje ty 0, 1, 2...
        st.dataframe(
            df, 
            column_config={"Forma": st.column_config.TextColumn("Forma")},
            hide_index=True,
            use_container_width=True
        )

    tab1, tab2, tab3 = st.tabs(["Celkové pořadí", "Pořadí dle průměru", "Archiv turnajů"])
    
    with tab1:
        st.write(render_table(df_final[['Jméno', 'Celkem', 'Max v kole', 'Forma']], 'Celkem'), unsafe_allow_html=True)
    with tab2:
        st.write(render_table(df_final[['Jméno', 'Průměr', 'Max v kole', 'Forma']], 'Průměr'), unsafe_allow_html=True)
    with tab3:
        st.subheader("Archiv turnajů")
        for f_name in sorted(os.listdir(DATA_FOLDER), reverse=True):
            if f_name.endswith('.json'): st.text(f"Turnaj: {f_name.replace('.json', '')}")
else:
    st.info("Žádná data k zobrazení.")