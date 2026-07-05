import streamlit as st
import pandas as pd
import json
import os
import streamlit.components.v1 as components

# --- KONFIGURACE - DEFINOVAT HNED NA ZAČÁTKU ---
DATA_FOLDER = 'Historie_turnaju_json'

# --- SIDEBAR - KONTAKT A LOGO ---
with st.sidebar:
    # Cesty nyní používají DATA_FOLDER, který je již známý
    try: 
        st.image(os.path.join(DATA_FOLDER, "Studio_Galax_1920x1080.png"), use_container_width=True)
    except Exception as e: 
        st.warning(f"Logo nenalezeno: {e}")
        
    st.markdown("### Studio Galax")
    st.markdown("🛠 **Vibe Coder: Jan Bugdol**")
    st.markdown("📧 [studiogalax.cz@gmail.com](mailto:studiogalax.cz@gmail.com)")
    st.divider()
        
    st.markdown("### 📱 Odkaz na statistiky")
    st.code("https://bit.ly/3SGN1ay", language=None)
        
    try: 
        st.image(os.path.join(DATA_FOLDER, "statistiky_qrcode.png"), width=150)
    except Exception as e: 
        st.info(f"QR kód nenalezen: {e}")

# --- FUNKCE PRO ZOBRAZENÍ TABULKY ---
def display_table(df, sort_by, columns):
    df = df.sort_values(by=sort_by, ascending=False).copy()
    df['Pořadí'] = df[sort_by].rank(method='min', ascending=False).astype(int)
    cols_to_show = ['Pořadí'] + columns
    df_show = df[cols_to_show].copy()
    
    for col in df_show.columns:
        if col == 'Celkem': df_show[col] = df_show[col].astype(int).astype(str)
        elif col == 'Průměr na hod': df_show[col] = df_show[col].apply(lambda x: f"{x:.2f}")

    html = """
    <style>
        .custom-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
        .custom-table th, .custom-table td { padding: 10px; border-bottom: 1px solid #ddd; text-align: center; }
        .custom-table td:nth-child(2) { text-align: left; white-space: nowrap; }
        .custom-table th { background-color: #f9f9f9; }
        .custom-table tr:nth-of-type(even) { background-color: #f2f2f2; }
    </style>
    <table class="custom-table">
        <thead><tr>""" + "".join([f"<th>{col}</th>" for col in df_show.columns]) + """</tr></thead>
        <tbody>""" + "".join(["<tr>" + "".join([f"<td>{val}</td>" for val in row]) + "</tr>" for _, row in df_show.iterrows()]) + """</tbody>
    </table>
    """
    with st.container(height=400):
        st.markdown(html, unsafe_allow_html=True)

# --- FUNKCE PRO TOP 10 NÁHOZŮ ---
def display_top_10_filtered(df_raw, limit):
    # Vyfiltrujeme pouze záznamy s daným limitem hodu
    df_filtered = df_raw[df_raw['Pocet_hodu'] == limit].copy()
    
    all_throws = []
    for _, row in df_filtered.iterrows():
        for throw in row['Surove_Body']:
            all_throws.append({"Jméno": row['Jméno'], "Body": throw})
    
    df_throws = pd.DataFrame(all_throws)
    if df_throws.empty:
        return "<p>Žádná data</p>"
        
    df_throws['Pořadí'] = df_throws['Body'].rank(method='min', ascending=False).astype(int)
    top_10 = df_throws.sort_values(by='Body', ascending=False).head(10).reset_index(drop=True)
    
    # HTML tabulka (stejná jako předtím)
    html = """
    <style>
        .custom-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.9em; }
        .custom-table th, .custom-table td { padding: 8px; border-bottom: 1px solid #ddd; text-align: center; }
        .custom-table td:nth-child(2) { text-align: left; }
        .custom-table th { background-color: #f9f9f9; }
    </style>
    <table class="custom-table">
        <thead><tr><th>Poř.</th><th>Jméno</th><th>Body</th></tr></thead>
        <tbody>""" + "".join([f"<tr><td>{row['Pořadí']}</td><td>{row['Jméno']}</td><td>{row['Body']}</td></tr>" for _, row in top_10.iterrows()]) + """</tbody>
    </table>
    """
    return html

# --- FUNKCE PRO JEDEN TURNAJ ---
def display_single_tournament(df_raw):
    turnaje_raw = sorted(df_raw['Turnaj'].unique(), reverse=True)
    turnaje_labels = [t.replace('turnaj_kuzelka_', '').replace('.json', '') for t in turnaje_raw]
    tournament_map = dict(zip(turnaje_labels, turnaje_raw))
    
    vybrane_datum = st.selectbox("Vyber datum turnaje:", turnaje_labels)
    
    df_turnaj = df_raw[df_raw['Turnaj'] == tournament_map[vybrane_datum]].copy()
    df_display = df_turnaj[['Jméno', 'Body']].sort_values(by='Body', ascending=False)
    df_display['Pořadí'] = df_display['Body'].rank(method='min', ascending=False).astype(int)
    df_display = df_display[['Pořadí', 'Jméno', 'Body']]
    
    html = """
    <style>
        .custom-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
        .custom-table th, .custom-table td { padding: 10px; border-bottom: 1px solid #ddd; text-align: center; }
        .custom-table td:nth-child(2) { text-align: left; }
        .custom-table th { background-color: #f9f9f9; }
        .custom-table tr:nth-of-type(even) { background-color: #f2f2f2; }
    </style>
    <table class="custom-table">
        <thead><tr><th>Pořadí</th><th>Jméno</th><th>Celkem bodů</th></tr></thead>
        <tbody>""" + "".join([f"<tr><td>{row['Pořadí']}</td><td>{row['Jméno']}</td><td>{row['Body']}</td></tr>" for _, row in df_display.iterrows()]) + """</tbody>
    </table>
    """
    # Použijeme stejný "těžký kalibr" komponentu
    components.html(html, height=400, scrolling=True)

# --- HLAVNÍ LOGIKA ---
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
    def process_player(group):
        group = group.sort_values('Turnaj')
        body_turnaje = group['Body'].tolist()
        surove_body = [s for sublist in group['Surove_Body'] for s in sublist]
        nazozy = pd.DataFrame({'kolo': [(i % 4) + 1 for i in range(len(surove_body))], 'hod': surove_body})
        best_kolo = nazozy.groupby('kolo')['hod'].mean().idxmax()
        forma = "▲" if len(body_turnaje) >= 2 and body_turnaje[-1] - body_turnaje[-2] >= 10 else ("▼" if len(body_turnaje) >= 2 and body_turnaje[-1] - body_turnaje[-2] <= -10 else "▬")
        return pd.Series({"Celkem": sum(body_turnaje), "Průměr na hod": sum(body_turnaje) / sum(group['Pocet_hodu']), "Best kolo": f"{best_kolo}. kolo", "Forma": forma})

    df_final = df_raw.groupby('Jméno').apply(process_player).reset_index()

    st.title("📊 Statistiky kuželkářského turnaje")
    _, col2, _ = st.columns([1, 6, 1])
    with col2:
        tab1, tab2, tab3, tab4 = st.tabs(["Celkové pořadí", "Pořadí dle průměru", "Top 10 náhozů", "Jeden turnaj"])
        with tab1: display_table(df_final, 'Celkem', ['Jméno', 'Celkem', 'Best kolo', 'Forma'])
        with tab2: display_table(df_final, 'Průměr na hod', ['Jméno', 'Průměr na hod', 'Best kolo', 'Forma'])
        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 🎯 Rekordy (10 hodů)")
                html_10 = display_top_10_filtered(df_raw, limit=10)
                components.html(html_10, height=400, scrolling=True)
            with col2:
                st.markdown("### 🎯 Rekordy (15 hodů)")
                html_15 = display_top_10_filtered(df_raw, limit=15)
                components.html(html_15, height=400, scrolling=True)
        with tab4: display_single_tournament(df_raw)
else:
    st.info("Žádná data k zobrazení.")