import streamlit as st
import pandas as pd
import json
import os
import math
import numpy as np
import streamlit.components.v1 as components
import re

# --- GLOBÁLNÍ CSS PRO TABULKY (Zebra + Scroll) ---
st.markdown("""
    <style>
    /* Zebra efekt pro všechny tabulky */
    div[data-testid="stDataFrame"] table tr:nth-of-type(even) {
        background-color: #f0f2f6 !important;
    }
    
    /* Vynucení barvy textu pro lepší čitelnost */
    div[data-testid="stDataFrame"] table tr {
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- KONFIGURACE ---
DATA_FOLDER = 'Historie_turnaju_json'

# --- FUNKCE ---
def display_table(df, sort_by, columns):
    if df.empty: return
    
    # KONTROLA: Pokud sloupec 'Průměr na hod' neexistuje, řadíme jen podle sort_by
    if 'Průměr na hod' in df.columns:
        df = df.sort_values(by=[sort_by, 'Průměr na hod'], ascending=[False, False]).copy()
    else:
        df = df.sort_values(by=[sort_by], ascending=[False]).copy()
    
    df['Pořadí'] = df[sort_by].rank(method='min', ascending=False).astype(int)
    
    cols_to_show = ['Pořadí'] + [c for c in columns if c in df.columns]
    df_show = df[cols_to_show].copy()
    
    # Formátování
    if 'Liga Body' in df_show.columns:
        df_show['Liga Body'] = (df_show['Liga Body'] / 10).round(1)
    if 'Max' in df_show.columns:
        df_show['Max'] = df_show['Max'].round(0)

    # Přejmenování pro hezčí tabulku
    rename_map = {'Pořadí': '', 'Průměr na hod': 'Ø/hod'}
    df_show = df_show.rename(columns=rename_map)

    # HTML generování (stejné jako předtím)
    html_table = df_show.to_html(index=False, classes='table-zebra', border=0)
    
    html_content = f"""
    <style>
        .table-zebra {{ width: 100%; border-collapse: collapse; font-family: sans-serif; table-layout: auto; }}
        .table-zebra tr:nth-of-type(even) {{ background-color: #f0f2f6; }}
        .table-zebra th, .table-zebra td {{ padding: 8px 10px; border-bottom: 1px solid #eee; white-space: nowrap; text-align: left; }}
        .table-zebra th:first-child, .table-zebra td:first-child {{ width: 30px; text-align: center; }}
        .table-zebra th {{ border-bottom: 2px solid #ddd; background-color: #ffffff; position: sticky; top: 0; }}
        .scroll-container {{ max-height: 500px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; }}
    </style>
    <div class="scroll-container">{html_table}</div>
    """
    components.html(html_content, height=510)

def get_rekordy(limit):
    vsechna_data = []
    
    # Projdeme JSON strukturu
    for team, hraci in data.get("teams", {}).items():
        for jmeno, body_list in hraci.items():
            # body_list je např. [32, 68, 45, 43]
            for i, body in enumerate(body_list):
                vsechna_data.append({
                    "Jméno": jmeno,
                    "Rekord": body,
                    "Datum": "Historie" # Tady můžeš doplnit datum z názvu souboru
                })
    
    if not vsechna_data: return pd.DataFrame(columns=["Jméno", "Max", "Datum"])
    
    df_rek = pd.DataFrame(vsechna_data)
    # Najdeme top 10 výkonů
    df_top10 = df_rek.sort_values('Rekord', ascending=False).head(10)
    return df_top10.rename(columns={'Rekord': 'Max', 'Datum': 'Datum'})
    


def vypocitat_pokerove_body(body, umisteni, pocet_hracu):
    return math.sqrt(pocet_hracu) * (body / math.log(umisteni + 1, 2))

# --- HLAVNÍ LOGIKA ---
all_stats = []
if os.path.exists(DATA_FOLDER):
    for file_name in [f for f in os.listdir(DATA_FOLDER) if f.endswith('.json')]:
        with open(os.path.join(DATA_FOLDER, file_name), 'r', encoding='utf-8') as f:
            data = json.load(f)
            limit_hodu = data.get("limit_hodu", 15)
            # Načtení dat
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
        
        # Průměr na turnaj, aby čísla nerostla do nekonečna
        prumerne_liga_body = (group['Ligove_Body'].sum() + max(0, (50 - odchylka) / 20) + skokan) / len(group)
        
        return pd.Series({"Liga Body": prumerne_liga_body, "Průměr na hod": group['Body'].sum() / celkem_hodů if celkem_hodů > 0 else 0})

    df_final = df_raw.groupby('Jméno').apply(process_player, include_groups=False).reset_index()

   # Vykreslení aplikace
    st.title("📊 Statistiky kuželkářského turnaje")
    
    tab1, tab2 = st.tabs(["📊 Ligová tabulka", "🏆 Top rekordy 10/15"])

    with tab1:
        PRUH_LIGY = 4.0
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown("### 🏆 Master Liga")
            display_table(df_final[df_final['Průměr na hod'] >= PRUH_LIGY], 'Liga Body', ['Jméno', 'Liga Body', 'Ø/hod'])
        with c2: 
            st.markdown("### 🥈 Challenge Liga")
            display_table(df_final[df_final['Průměr na hod'] < PRUH_LIGY], 'Liga Body', ['Jméno', 'Liga Body', 'Ø/hod'])

    with tab2:
        # Rozdělíme záložku na dva sloupce
        c1, c2 = st.columns(2)
    
        with c1:
            st.markdown("### 🔥 Top 10 (10 hodů)")
            display_table(get_rekordy(10), 'Max', ['Jméno', 'Max', 'Datum'])
        
        with c2:
            st.markdown("### 🔥 Top 10 (15 hodů)")
            display_table(get_rekordy(15), 'Max', ['Jméno', 'Max', 'Datum'])

else:
    st.info("Žádná data k zobrazení.")