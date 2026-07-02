import streamlit as st
import pandas as pd
import json
import os

# --- FUNKCE PRO ZOBRAZENÍ TABULKY S "ZEBROVÁNÍM" ---
def display_table(df, sort_by, columns):
    df = df.sort_values(by=sort_by, ascending=False).copy()
    df['Pořadí'] = df[sort_by].rank(method='min', ascending=False).astype(int)
    
    cols_to_show = ['Pořadí'] + columns
    df_show = df[cols_to_show].copy()
    
    # Formátování
    for col in df_show.columns:
        if col == 'Celkem':
            df_show[col] = df_show[col].astype(int)
        elif col == 'Průměr na hod':
            df_show[col] = df_show[col].map('{:.2f}'.format)
            
    # 1. Definice barevné zebry přes styler
    def style_zebra(df):
        # Vytvoříme prázdný DataFrame se stejným tvarem
        style = pd.DataFrame('', index=df.index, columns=df.columns)
        # Obarvíme sudé řádky
        style.iloc[1::2, :] = 'background-color: #f2f2f2'
        return style

    # 2. Vykreslení
    st.dataframe(
        df_show.style.apply(style_zebra, axis=None), 
        hide_index=True, 
        use_container_width=True,
        height=400
    )

# --- HLAVNÍ LOGIKA ---
DATA_FOLDER = 'Historie_turnaju_json'
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
                            "Surove_Body": scores,
                            "Turnaj": file_name,
                            "Pocet_hodu": len(scores) * limit_hodu
                        })

if all_stats:
    df_raw = pd.DataFrame(all_stats)
    
    # Výpočet statistik
    def process_player(group):
        group = group.sort_values('Turnaj')
        body_turnaje = group['Body'].tolist()
        surove_body = [s for sublist in group['Surove_Body'] for s in sublist]
        
        nazozy = pd.DataFrame({'kolo': [(i % 4) + 1 for i in range(len(surove_body))], 'hod': surove_body})
        best_kolo = nazozy.groupby('kolo')['hod'].mean().idxmax()
        
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

    # Zobrazení
    st.title("📊 Statistiky kuželkářského turnaje")
    
    # Použijeme sloupce pro zúžení tabulky
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        tab1, tab2 = st.tabs(["Celkové pořadí", "Pořadí dle průměru"])
        with tab1:
            display_table(df_final, 'Celkem', ['Jméno', 'Celkem', 'Best kolo', 'Forma'])
        with tab2:
            display_table(df_final, 'Průměr na hod', ['Jméno', 'Průměr na hod', 'Best kolo', 'Forma'])
else:
    st.info("Žádná data k zobrazení.")
