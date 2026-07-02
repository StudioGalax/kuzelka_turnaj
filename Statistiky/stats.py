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
                limit_hodu = data.get("limit_hodu", 15)  # Získání limitu hodů
                for team in data.get('teams', {}).values():
                    for p_name, scores in team.items():
                        all_stats.append({
                            "Jméno": p_name.strip(), 
                            "Body": scores, 
                            "Limit": limit_hodu
                        })

if all_stats:
    df_raw = pd.DataFrame(all_stats)
    
    # 2. LOGIKA STATISTIK
    def process_player(group):
        # Spojíme všechny náhozy všech turnajů
        all_body = [s for sublist in group['Body'] for s in sublist]
        # Spočítáme celkový počet hodů (součet limitů všech kol)
        total_hody = sum(group['Limit'])
        
        # Logika pro "Nejoblíbenější kolo" (1-4) podle průměru na jeden hod
        nazozy = pd.DataFrame({'kolo': [(i % 4) + 1 for i in range(len(all_body))], 'hod': all_body})
        avg_per_kolo = nazozy.groupby('kolo')['hod'].mean()
        best_kolo = avg_per_kolo.idxmax()
        
        # Forma
        forma = "➡️"
        if len(all_body) >= 3:
            rozdil = all_body[-1] - (sum(all_body[-3:-1]) / 2)
            if rozdil >= 10: forma = "⬆️"
            elif rozdil <= -10: forma = "⬇️"
            
        return pd.Series({
            "Celkem": sum(all_body),
            "Průměr na hod": sum(all_body) / total_hody,
            "Best kolo": f"{best_kolo}. kolo",
            "Forma": forma
        })

    df_final = df_raw.groupby('Jméno').apply(process_player).reset_index()

    # 3. VÝSTUP (ČISTÁ TABULKA)
    def display_table(df, sort_by):
        df = df.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
        df.insert(0, 'Pořadí', range(1, len(df) + 1))
        
        # Formátování (pouze pokud sloupce existují)
        if 'Průměr na hod' in df.columns:
            df['Průměr na hod'] = df['Průměr na hod'].map('{:.2f}'.format)
            
        # hide_index=True skryje ty 0, 1, 2...
        st.dataframe(df, hide_index=True, use_container_width=True)

    tab1, tab2 = st.tabs(["Celkové pořadí", "Pořadí dle průměru na hod"])
    with tab1:
        display_table(df_final[['Jméno', 'Celkem', 'Best kolo', 'Forma']], 'Celkem')
    with tab2:
        display_table(df_final[['Jméno', 'Průměr na hod', 'Best kolo', 'Forma']], 'Průměr na hod')
else:
    st.info("Žádná data k zobrazení.")