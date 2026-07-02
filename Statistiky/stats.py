import streamlit as st
import pandas as pd
import json
import os

# --- FUNKCE PRO ZOBRAZENÍ TABULKY S "ZEBROVÁNÍM" ---
def display_table(df, sort_by, columns):
    df = df.sort_values(by=sort_by, ascending=False).copy()
    df['Pořadí'] = df[sort_by].rank(method='min', ascending=False).astype(int)
    
    # Vybereme jen sloupce, které chceme
    cols_to_show = ['Pořadí'] + columns
    df_show = df[cols_to_show].copy()
    
    # Formátování (převod na text)
    if 'Celkem' in df_show.columns:
        df_show['Celkem'] = df_show['Celkem'].astype(int).astype(str)
    if 'Průměr na hod' in df_show.columns:
        df_show['Průměr na hod'] = df_show['Průměr na hod'].apply(lambda x: f"{x:.2f}")

    # Definice sloupců
    col_config = {
        "Pořadí": st.column_config.TextColumn("Pořadí", width="small"),
        "Jméno": st.column_config.TextColumn("Jméno", width="medium"),
        "Celkem": st.column_config.TextColumn("Celkem", width="small"),
        "Průměr na hod": st.column_config.TextColumn("∅ na hod", width="small"),
        "Best kolo": st.column_config.TextColumn("Best kolo", width="small"),
        "Forma": st.column_config.TextColumn("Forma", width="small")
    }
    
    # 3. Zobrazení: hide_index=True a pevná výška
    st.dataframe(
        df_show, 
        hide_index=True,        # Toto odstraní ten sloupec s čísly 4, 14, 0...
        use_container_width=True, 
        column_config=col_config,
        height=400             # Tabulka bude vysoká 400 pixelů, zbytek bude mít posuvník
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
