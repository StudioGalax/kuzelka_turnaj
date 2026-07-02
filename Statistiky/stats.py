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
    
    for col in df_show.columns:
        if col == 'Celkem':
            df_show[col] = df_show[col].astype(int).astype(str)
        elif col == 'Průměr na hod':
            df_show[col] = df_show[col].apply(lambda x: f"{x:.2f}")

    html = """
    <style>
        .custom-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
        .custom-table th, .custom-table td { padding: 10px; border-bottom: 1px solid #ddd; }
        .custom-table td:nth-child(2), .custom-table th:nth-child(2) { text-align: left; }
        .custom-table th, .custom-table td { text-align: center; }
        .custom-table th { background-color: #f9f9f9; }
        .custom-table tr:nth-of-type(even) { background-color: #f2f2f2; }
    </style>
    <table class="custom-table">
        <thead><tr>""" + "".join([f"<th>{col}</th>" for col in df_show.columns]) + """</tr></thead>
        <tbody>""" + "".join([
            "<tr>" + "".join([f"<td>{val}</td>" for val in row]) + "</tr>" 
            for _, row in df_show.iterrows()
        ]) + """</tbody>
    </table>
    """
    with st.container(height=400):
        st.markdown(html, unsafe_allow_html=True)

# --- FUNKCE PRO TOP 10 NÁHOZŮ ---
def display_top_10_hody(df_raw):
    # Rozbalíme hody
    all_throws = []
    for _, row in df_raw.iterrows():
        for throw in row['Surove_Body']:
            all_throws.append({"Jméno": row['Jméno'], "Body": throw})
    
    df_throws = pd.DataFrame(all_throws)
    
    # 1. Seřadíme a vytvoříme pořadí (method='min' řeší shody)
    df_throws = df_throws.sort_values(by='Body', ascending=False).copy()
    df_throws['Pořadí'] = df_throws['Body'].rank(method='min', ascending=False).astype(int)
    
    # 2. Vezmeme top 10 (zde pozor: pokud má 10. a 11. místo stejný počet bodů, 
    # metoda 'min' nám jich může vrátit více než 10, proto uděláme .head(10))
    top_10 = df_throws.head(10).reset_index(drop=True)
    
    # HTML tabulka
    html = """
    <style>
        .custom-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
        .custom-table th, .custom-table td { padding: 10px; border-bottom: 1px solid #ddd; text-align: center; }
        .custom-table td:nth-child(2) { text-align: left; }
        .custom-table th { background-color: #f9f9f9; }
        .custom-table tr:nth-of-type(even) { background-color: #f2f2f2; }
    </style>
    <table class="custom-table">
        <thead><tr><th>Pořadí</th><th>Jméno</th><th>Body v hodu</th></tr></thead>
        <tbody>""" + "".join([
            f"<tr><td>{row['Pořadí']}</td><td>{row['Jméno']}</td><td>{row['Body']}</td></tr>" 
            for _, row in top_10.iterrows()
        ]) + """</tbody>
    </table>
    """
    with st.container(height=400):
        st.markdown(html, unsafe_allow_html=True)
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
        # ZDE PŘIDÁVÁME TŘETÍ TAB
        tab1, tab2, tab3 = st.tabs(["Celkové pořadí", "Pořadí dle průměru", "Top 10 náhozů"])
        with tab1:
            display_table(df_final, 'Celkem', ['Jméno', 'Celkem', 'Best kolo', 'Forma'])
        with tab2:
            display_table(df_final, 'Průměr na hod', ['Jméno', 'Průměr na hod', 'Best kolo', 'Forma'])
        with tab3:
            display_top_10_hody(df_raw)
else:
    st.info("Žádná data k zobrazení.")
