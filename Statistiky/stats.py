from tokenize import group
import streamlit as st
import pandas as pd
import json
import os
import streamlit.components.v1 as components
import math
import numpy as np

# --- KONFIGURACE ---
DATA_FOLDER = 'Historie_turnaju_json'

# --- SIDEBAR ---
with st.sidebar:
    try: 
        st.image(os.path.join(DATA_FOLDER, "Studio_Galax_1920x1080.png"), use_container_width=True)
    except: pass
    st.markdown("### Studio Galax")
    st.markdown("🛠 **Vibe Coder: Jan Bugdol**")
    st.divider()
    st.markdown("### 📱 Odkaz na statistiky")
    st.code("https://bit.ly/3SGN1ay", language=None)

# --- FUNKCE ---
def display_table(df, sort_by, columns):
    if df.empty: return
    df = df.sort_values(by=sort_by, ascending=False).copy()
    df['Pořadí'] = df[sort_by].rank(method='min', ascending=False).astype(int)
    cols_to_show = ['Pořadí'] + [c for c in columns if c in df.columns]
    df_show = df[cols_to_show].copy()
    
    for col in df_show.columns:
        if 'Průměr' in col or 'Body' in col and 'Liga' in col: 
            df_show[col] = df_show[col].apply(lambda x: f"{x:.2f}")

    html = """<style>.custom-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
        .custom-table th, .custom-table td { padding: 8px; border-bottom: 1px solid #ddd; text-align: center; }
        .custom-table th { background-color: #f9f9f9; }</style>
        <table class="custom-table"><thead><tr>""" + "".join([f"<th>{col}</th>" for col in df_show.columns]) + """</tr></thead>
        <tbody>""" + "".join(["<tr>" + "".join([f"<td>{val}</td>" for val in row]) + "</tr>" for _, row in df_show.iterrows()]) + """</tbody></table>"""
    st.markdown(html, unsafe_allow_html=True)

def vypocitat_pokerove_body(body, umisteni, pocet_hracu):
    return math.sqrt(pocet_hracu) * (body / (umisteni ** 3))

def display_top_10_filtered(df_raw, limit):
    df_filtered = df_raw[df_raw['limit_hodu'] == limit].copy()
    if df_filtered.empty: return "<p style='text-align:center;'>Zatím nejsou data</p>"
    all_throws = [{"Jméno": row['Jméno'], "Body": throw} for _, row in df_filtered.iterrows() for throw in row['Surove_Body']]
    df_throws = pd.DataFrame(all_throws)
    top_10 = df_throws.sort_values(by='Body', ascending=False).head(10).reset_index(drop=True)
    return """<table style='width:100%; font-size:0.9em;'><tr><th>Jméno</th><th>Body</th></tr>""" + "".join([f"<tr><td>{row['Jméno']}</td><td>{row['Body']}</td></tr>" for _, row in top_10.iterrows()]) + "</table>"

# --- HLAVNÍ LOGIKA ---
all_stats = []
if os.path.exists(DATA_FOLDER):
    for file_name in [f for f in os.listdir(DATA_FOLDER) if f.endswith('.json')]:
        with open(os.path.join(DATA_FOLDER, file_name), 'r', encoding='utf-8') as f:
            data = json.load(f)
            limit_hodu = data.get("limit_hodu", 15)
            turnaj_hraci = [{"Jméno": n.strip(), "Body": sum(s), "Surove_Body": s} for team in data.get('teams', {}).values() for n, s in team.items()]
            turnaj_hraci.sort(key=lambda x: x['Body'], reverse=True)
            for idx, hrac in enumerate(turnaj_hraci):
                all_stats.append({**hrac, "Ligove_Body": vypocitat_pokerove_body(hrac['Body'], idx + 1, len(turnaj_hraci)), "Turnaj": file_name, "limit_hodu": limit_hodu})

if all_stats:
    df_raw = pd.DataFrame(all_stats)
    def process_player(group):
        vsechny_hody = [h for sublist in group['Surove_Body'] for h in sublist]
        celkem_hodů = sum(len(row['Surove_Body']) * row['limit_hodu'] for _, row in group.iterrows())
        odchylka = np.std(vsechny_hody) if len(vsechny_hody) > 0 else 0
        skokan = 0
        if len(group) >= 2:
            s = group.sort_values('Turnaj')
            skokan = max(0, (s.iloc[-1]['Body'] / (len(s.iloc[-1]['Surove_Body']) * s.iloc[-1]['limit_hodu']) - s.iloc[-2]['Body'] / (len(s.iloc[-2]['Surove_Body']) * s.iloc[-2]['limit_hodu'])) * 2)
        return pd.Series({"Turnajů": len(group), "Liga Body": group['Ligove_Body'].sum() + max(0, (50-odchylka)/20) + skokan, "Průměr na hod": group['Body'].sum() / celkem_hodů if celkem_hodů > 0 else 0, "Forma": "▲" if skokan > 0.5 else "▬"})

    df_final = df_raw.groupby('Jméno').apply(process_player, include_groups=False).reset_index()

    st.title("📊 Statistiky kuželkářského turnaje")
    tab1, tab2, tab3 = st.tabs(["🏆 LIGY (Master & Challenge)", "🎯 Top 10 náhozů", "📅 Detail turnaje"])
    
    with tab1:
        PRUH_LIGY = 4.0
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🏆 Master Liga")
            display_table(df_final[df_final['Průměr na hod'] >= PRUH_LIGY], 'Liga Body', ['Jméno', 'Liga Body', 'Průměr na hod'])
        with col2:
            st.markdown("### 🥈 Challenge Liga")
            display_table(df_final[df_final['Průměr na hod'] < PRUH_LIGY], 'Liga Body', ['Jméno', 'Liga Body', 'Průměr na hod'])
    
    with tab2:
        c1, c2 = st.columns(2)
        with c1: st.markdown("### 🎯 10 hodů"); components.html(display_top_10_filtered(df_raw, 10), height=300)
        with c2: st.markdown("### 🎯 15 hodů"); components.html(display_top_10_filtered(df_raw, 15), height=300)
    
    with tab3:
        # Tady si doplň svoji funkci pro detail turnaje
        st.info("Zde bude detail turnaje.")
else:
    st.info("Žádná data k zobrazení.")