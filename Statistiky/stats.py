import streamlit as st
import pandas as pd
import json
import os
import math
import numpy as np

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
    
    # 1. Seřazení a pořadí
    df = df.sort_values(by=[sort_by, 'Průměr na hod'], ascending=[False, False]).copy()
    df['Pořadí'] = df[sort_by].rank(method='min', ascending=False).astype(int)
    
    # 2. Příprava sloupců a formátování
    cols_to_show = ['Pořadí'] + [c for c in columns if c in df.columns]
    df_show = df[cols_to_show].copy()
    
    if 'Liga Body' in df_show.columns:
        df_show['Liga Body'] = (df_show['Liga Body'] / 10).round(1)

    # 3. Zebra pomocí CSS
    # Vynechali jsme .background_gradient, který dělal tu neplechu
    st.dataframe(
        df_show,
        hide_index=True,
        use_container_width=True,
        height=500,
        column_config={
            "Liga Body": st.column_config.NumberColumn(format="%.1f"),
            "Průměr na hod": st.column_config.NumberColumn(format="%.2f")
        }
    )
    


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

    st.title("📊 Statistiky kuželkářského turnaje")
    
    PRUH_LIGY = 4.0
    c1, c2 = st.columns(2)
    with c1: 
        st.markdown("### 🏆 Master Liga")
        display_table(df_final[df_final['Průměr na hod'] >= PRUH_LIGY], 'Liga Body', ['Jméno', 'Liga Body', 'Průměr na hod'])
    with c2: 
        st.markdown("### 🥈 Challenge Liga")
        display_table(df_final[df_final['Průměr na hod'] < PRUH_LIGY], 'Liga Body', ['Jméno', 'Liga Body', 'Průměr na hod'])
else:
    st.info("Žádná data k zobrazení.")