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
                limit_hodu = data.get("limit_hodu", 15)
                for team in data.get('teams', {}).values():
                    for p_name, scores in team.items():
                        # Uložíme i název souboru pro identifikaci turnaje
                        all_stats.append({
                            "Jméno": p_name.strip(), 
                            "Body": sum(scores), # Celkem za turnaj
                            "Turnaj": file_name,
                            "Limit": limit_hodu,
                            "Pocet_hodu": len(scores) * limit_hodu
                        })

if all_stats:
    df_raw = pd.DataFrame(all_stats)
    
    # 2. LOGIKA STATISTIK
    def process_player(group):
        # Seřadíme turnaje podle názvu, aby forma dávala smysl v čase
        group = group.sort_values('Turnaj')
        body_turnaje = group['Body'].tolist()
        celkem_bodu = sum(body_turnaje)
        celkem_hodu = sum(group['Pocet_hodu'])
        
        # Forma: porovnání posledního turnaje s předchozím
        forma = "➡️"
        if len(body_turnaje) >= 2:
            rozdil = body_turnaje[-1] - body_turnaje[-2]
            if rozdil >= 10: forma = "⬆️"
            elif rozdil <= -10: forma = "⬇️"
            
        # Best kolo: průměr na hod v rámci turnajů (kolo 1-4)
        # Zjednodušeno: vezmeme poslední turnaj jako reprezentativní
        return pd.Series({
            "Celkem": celkem_bodu,
            "Průměr na hod": celkem_bodu / celkem_hodu if celkem_hodu > 0 else 0,
            "Forma": forma
        })

    df_final = df_raw.groupby('Jméno').apply(process_player).reset_index()

    # 3. VÝSTUP
    def display_table(df, sort_by):
        df = df.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
        df.insert(0, 'Pořadí', range(1, len(df) + 1))
        
        if 'Průměr na hod' in df.columns:
            df['Průměr na hod'] = df['Průměr na hod'].map('{:.2f}'.format)
            
        st.dataframe(df, hide_index=True, use_container_width=True)

    tab1, tab2 = st.tabs(["Celkové pořadí", "Pořadí dle průměru na hod"])
    with tab1:
        display_table(df_final[['Jméno', 'Celkem', 'Forma']], 'Celkem')
    with tab2:
        display_table(df_final[['Jméno', 'Průměr na hod', 'Forma']], 'Průměr na hod')
else:
    st.info("Žádná data k zobrazení.")