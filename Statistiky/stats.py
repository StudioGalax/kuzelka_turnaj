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
                        all_stats.append({
                            "Jméno": p_name.strip(),
                            "Body": sum(scores),
                            "Surove_Body": scores, # Seznam náhozů pro výpočet Best kola
                            "Turnaj": file_name,
                            "Pocet_hodu": len(scores) * limit_hodu
                        })

if all_stats:
    df_raw = pd.DataFrame(all_stats)
    
    # 2. LOGIKA STATISTIK
    def process_player(group):
        group = group.sort_values('Turnaj')
        body_turnaje = group['Body'].tolist()
        surove_body = [s for sublist in group['Surove_Body'] for s in sublist]
        
        # Best kolo (průměr na hod v kole 1-4 napříč turnaji)
        nazozy = pd.DataFrame({'kolo': [(i % 4) + 1 for i in range(len(surove_body))], 'hod': surove_body})
        best_kolo = nazozy.groupby('kolo')['hod'].mean().idxmax()
        
        # Forma (▲, ▼, ▬)
        forma = "▬"
        if len(body_turnaje) >= 2:
            rozdil = body_turnaje[-1] - body_turnaje[-2]
            if rozdil >= 10: forma = "▲"
            elif rozdil <= -10: forma = "▼"
            
        return pd.Series({
            "Celkem": sum(body_turnaje),
            "Průměr na hod": sum(body_turnaje) / sum(group['Pocet_hodu']),
            "Best kolo": f"{best_kolo}. kolo",
            "Forma": forma
        })

    df_final = df_raw.groupby('Jméno').apply(process_player).reset_index()

    # 3. VÝSTUP S BARVAMI
    def display_table(df, sort_by):
        df = df.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
        df.insert(0, 'Pořadí', range(1, len(df) + 1))
        
        # Konfigurace vzhledu sloupců pro lepší zarovnání a šířku
        col_config = {
            "Pořadí": st.column_config.NumberColumn("Pořadí", width="small"),
            "Jméno": st.column_config.TextColumn("Jméno", width="medium"),
            "Celkem": st.column_config.NumberColumn("Celkem", format="%d", width="small"),
            "Průměr na hod": st.column_config.NumberColumn("Průměr na hod", format="%.2f", width="small"),
            "Best kolo": st.column_config.TextColumn("Best kolo", width="small"),
            "Forma": st.column_config.TextColumn("Forma", width="small")
        }
        
        st.dataframe(
            df, 
            hide_index=True, 
            use_container_width=True, 
            column_config=col_config
        )

    tab1, tab2 = st.tabs(["Celkové pořadí", "Pořadí dle průměru"])
    with tab1:
        display_table(df_final[['Jméno', 'Celkem', 'Best kolo', 'Forma']], 'Celkem')
    with tab2:
        display_table(df_final[['Jméno', 'Průměr na hod', 'Best kolo', 'Forma']], 'Průměr na hod')
else:
    st.info("Žádná data k zobrazení.")