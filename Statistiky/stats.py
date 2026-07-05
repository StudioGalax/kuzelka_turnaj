from tokenize import group

import streamlit as st
import pandas as pd
import json
import os
import streamlit.components.v1 as components
import math
import numpy as np

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
    
    # Zde zajistíme, aby se zobrazily jen ty sloupce, které skutečně existují
    cols_to_show = ['Pořadí'] + [c for c in columns if c in df.columns]
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
    # Důležité: používáme klíč 'limit_hodu', který jsme uložili v kroku 1
    df_filtered = df_raw[df_raw['limit_hodu'] == limit].copy()
    
    if df_filtered.empty:
        return "<p style='text-align:center;'>Zatím nejsou data</p>"
    
    all_throws = []
    for _, row in df_filtered.iterrows():
        for throw in row['Surove_Body']:
            all_throws.append({"Jméno": row['Jméno'], "Body": throw})
    
    df_throws = pd.DataFrame(all_throws)
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

def vypocitat_pokerove_body(body, umisteni, pocet_hracu):
    # tvůj vzorec: Body = sqrt(n) * (v / p^3)
    return math.sqrt(pocet_hracu) * (body / (umisteni ** 3))

# --- HLAVNÍ LOGIKA ---
all_stats = []
if os.path.exists(DATA_FOLDER):
    for file_name in os.listdir(DATA_FOLDER):
        if file_name.endswith('.json'):
            with open(os.path.join(DATA_FOLDER, file_name), 'r', encoding='utf-8') as f:
                data = json.load(f)
                limit_hodu = data.get("limit_hodu", 15)
                
                # Příprava na pokerové bodování (seřadíme hráče v turnaji)
                turnaj_hraci = []
                for team in data.get('teams', {}).values():
                    for p_name, scores in team.items():
                        turnaj_hraci.append({"Jméno": p_name.strip(), "Body": sum(scores), "Surove_Body": scores})
                
                turnaj_hraci.sort(key=lambda x: x['Body'], reverse=True)
                
                # Výpočet bodů pro každého v turnaji
                pocet_hracu = len(turnaj_hraci)
                for idx, hrac in enumerate(turnaj_hraci):
                    umisteni = idx + 1
                    all_stats.append({
                        "Jméno": hrac['Jméno'],
                        "Body": hrac['Body'],
                        "Ligove_Body": vypocitat_pokerove_body(hrac['Body'], umisteni, pocet_hracu),
                        "Surove_Body": hrac['Surove_Body'],
                        "Turnaj": file_name,
                        "limit_hodu": limit_hodu
                    })

if all_stats:
    df_raw = pd.DataFrame(all_stats)
    
    def process_player(group):
        vsechny_hody = [h for sublist in group['Surove_Body'] for h in sublist]
        celkem_hodů = sum(len(row['Surove_Body']) * row['limit_hodu'] for _, row in group.iterrows())
        prumer = group['Body'].sum() / celkem_hodů if celkem_hodů > 0 else 0
        
        # Bonusy
        odchylka = np.std(vsechny_hody) if len(vsechny_hody) > 0 else 0
        vyrovnanost_bonus = max(0, (50 - odchylka) / 20) # Koření
        
        skokan_bonus = 0
        if len(group) >= 2:
            s = group.sort_values('Turnaj')
            posledni = s.iloc[-1]['Body'] / (len(s.iloc[-1]['Surove_Body']) * s.iloc[-1]['limit_hodu'])
            predchozi = s.iloc[-2]['Body'] / (len(s.iloc[-2]['Surove_Body']) * s.iloc[-2]['limit_hodu'])
            skokan_bonus = max(0, (posledni - predchozi) * 2)
            
        return pd.Series({
            "Turnajů": len(group),
            "Celkem bodů": group['Body'].sum(),
            "Liga Body": group['Ligove_Body'].sum() + vyrovnanost_bonus + skokan_bonus,
            "Průměr na hod": prumer,
            "Forma": "▲" if skokan_bonus > 0.5 else "▬"
        })

    df_final = df_raw.groupby('Jméno').apply(process_player, include_groups=False).reset_index()

    # --- ZOBRAZENÍ DVOU LIG ---
    st.title("📊 Statistiky kuželkářského turnaje")
    PRUH_LIGY = 4.0
    df_master = df_final[df_final['Průměr na hod'] >= PRUH_LIGY].copy()
    df_challenge = df_final[df_final['Průměr na hod'] < PRUH_LIGY].copy()

    with st.tabs(["Celkové pořadí", "Top 10", "Detail turnaje"])[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🏆 Master Liga")
            display_table(df_master, 'Liga Body', ['Jméno', 'Liga Body', 'Průměr na hod'])
        with col2:
            st.markdown("### 🥈 Challenge Liga")
            display_table(df_challenge, 'Liga Body', ['Jméno', 'Liga Body', 'Průměr na hod'])

    st.title("📊 Statistiky kuželkářského turnaje")
    _, col2, _ = st.columns([1, 6, 1])
    with col2:
        tab1, tab2, tab3, tab4 = st.tabs(["Celkové pořadí", "Pořadí dle průměru", "Top 10 náhozů", "Jeden turnaj"])
        
        # Opravili jsme názvy sloupců, podle kterých se řadí ('Celkem bodů' místo 'Celkem')
        with tab1:
            display_table(df_final, 'Celkem bodů', ['Jméno', 'Turnajů', 'Celkem bodů', 'Průměr na hod', 'Forma'])
        with tab2:
            display_table(df_final, 'Průměr na hod', ['Jméno', 'Turnajů', 'Celkem bodů', 'Průměr na hod', 'Forma'])
        with tab3:
            # Tady využijeme tvůj nový kód pro dvě tabulky vedle sebe
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<h3 style='text-align: center;'>🎯 10 hodů</h3>", unsafe_allow_html=True)
                components.html(display_top_10_filtered(df_raw, 10), height=400, scrolling=True)
            with col2:
                st.markdown("<h3 style='text-align: center;'>🎯 15 hodů</h3>", unsafe_allow_html=True)
                components.html(display_top_10_filtered(df_raw, 15), height=400, scrolling=True)
        with tab4:
            display_single_tournament(df_raw)
else:
    st.info("Žádná data k zobrazení.")