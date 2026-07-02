import streamlit as st
import pandas as pd
import json
import os

DATA_FOLDER = 'Historie_turnaju_json'
st.set_page_config(page_title="Kuželky - Statistiky", layout="wide")
st.title("📊 Statistiky kuželkářského turnaje")

# 1. NAČTENÍ DAT
all_stats = []
if os.path.exists(DATA_FOLDER):
    for file_name in os.listdir(DATA_FOLDER):
        if file_name.endswith('.json'):
            with open(os.path.join(DATA_FOLDER, file_name), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for team in data.get('teams', {}).values():
                    for p_name, scores in team.items():
                        # scores je seznam [hod1, hod2, hod3, hod4]
                        all_stats.append({"Jméno": p_name.strip(), "Body": scores})

if all_stats:
    df_raw = pd.DataFrame(all_stats)
    
    # Seskupíme všechna data hráče dohromady (pokud hrál více turnajů)
    def aggregate_player(group):
        # Spojíme všechny seznamy náhozů do jedné dlouhé řady
        all_scores = [score for sublist in group['Body'] for score in sublist]
        return pd.Series({"Všechny_náhozy": all_scores})

    df_grouped = df_raw.groupby('Jméno').apply(aggregate_player).reset_index()

    # 2. LOGIKA STATISTIK
    def get_stats(row):
        body = row['Všechny_náhozy']
        # Pořadí kol 1-4 se opakuje (modulo 4)
        nazozy_po_kolech = pd.DataFrame({'kolo': [(i % 4) + 1 for i in range(len(body))], 'hod': body})
        avg_per_kolo = nazozy_po_kolech.groupby('kolo')['hod'].mean()
        
        best_kolo_idx = avg_per_kolo.idxmax()
        best_kolo_val = avg_per_kolo.max()
        
        # Forma (poslední 3 náhozy vs průměr)
        forma = "➡️"
        if len(body) >= 3:
            rozdil = body[-1] - (sum(body[-3:-1]) / 2)
            if rozdil >= 10: forma = "⬆️"
            elif rozdil <= -10: forma = "⬇️"
            
        return pd.Series({
            "Celkem": sum(body),
            "Průměr": sum(body) / len(body),
            "Best kolo": f"{best_kolo_idx}. kolo",
            "Forma": forma
        })

    df_final = df_grouped.apply(get_stats, axis=1).reset_index()
    df_final['Jméno'] = df_grouped['Jméno']

    # 3. VÝSTUP (ČISTÁ TABULKA)
    def display_table(df, sort_by):
        df = df.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
        df.insert(0, 'Pořadí', range(1, len(df) + 1))
        df['Průměr'] = df['Průměr'].map('{:.1f}'.format)
        # hide_index=True konečně odstraní ty nuly!
        st.dataframe(df, hide_index=True, use_container_width=True)

    tab1, tab2 = st.tabs(["Celkové pořadí", "Pořadí dle průměru"])
    with tab1:
        display_table(df_final[['Jméno', 'Celkem', 'Best kolo', 'Forma']], 'Celkem')
    with tab2:
        display_table(df_final[['Jméno', 'Průměr', 'Best kolo', 'Forma']], 'Průměr')
else:
    st.info("Žádná data k zobrazení.")