import streamlit as st
import pandas as pd
import json
import os
import math
import numpy as np
import streamlit.components.v1 as components
import re
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="Statistiky kuželkářského turnaje", layout="wide")

# --- GLOBÁLNÍ CSS PRO TABULKY A METRIKY ---
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

    /* Přehledné a kompaktní statistické karty / metriky */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 19px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #4a5568 !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- KONFIGURACE CESTY K DATŮM ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists('Historie_turnaju_json'):
    DATA_FOLDER = 'Historie_turnaju_json'
elif os.path.exists(os.path.join(os.path.dirname(BASE_DIR), 'Historie_turnaju_json')):
    DATA_FOLDER = os.path.join(os.path.dirname(BASE_DIR), 'Historie_turnaju_json')
elif os.path.exists(os.path.join(BASE_DIR, 'Historie_turnaju_json')):
    DATA_FOLDER = os.path.join(BASE_DIR, 'Historie_turnaju_json')
else:
    DATA_FOLDER = 'Historie_turnaju_json'

# --- FUNKCE ---
def display_table(df, sort_by, columns, max_rows=10):
    if df.empty: return
    
    # KONTROLA a řazení:
    if sort_by != 'Průměr na hod' and 'Průměr na hod' in df.columns:
        df = df.sort_values(by=[sort_by, 'Průměr na hod'], ascending=[False, False]).copy()
    elif sort_by == 'Průměr na hod' and 'Liga Body' in df.columns:
        df = df.sort_values(by=['Průměr na hod', 'Liga Body'], ascending=[False, False]).copy()
    else:
        df = df.sort_values(by=[sort_by], ascending=[False]).copy()
    
    df['Pořadí'] = df[sort_by].rank(method='min', ascending=False).astype(int)
    
    # Mapování názvů sloupců (pokud bylo předáno 'Ø/hod' místo 'Průměr na hod')
    col_mapping = {'Ø/hod': 'Průměr na hod'}
    actual_cols = [col_mapping.get(c, c) for c in columns]
    
    cols_to_show = ['Pořadí'] + [c for c in actual_cols if c in df.columns]
    df_show = df[cols_to_show].copy()
    
    # Formátování
    if 'Liga Body' in df_show.columns:
        df_show['Liga Body'] = (df_show['Liga Body'] / 10).round(1)
    if 'Průměr na hod' in df_show.columns:
        df_show['Průměr na hod'] = df_show['Průměr na hod'].round(2)
    if 'Max' in df_show.columns:
        df_show['Max'] = df_show['Max'].round(0)

    # Přejmenování pro hezčí tabulku
    rename_map = {'Pořadí': '', 'Průměr na hod': 'Ø/hod'}
    df_show = df_show.rename(columns=rename_map)

    # Výpočet výšky (max 10 hráčů viditelných, pak rolování)
    row_count = len(df_show)
    visible_rows = min(row_count, max_rows)
    container_max_height = 42 + max_rows * 37
    calc_height = 42 + visible_rows * 37 + 10
    iframe_height = min(calc_height, container_max_height + 15)

    # HTML generování
    html_table = df_show.to_html(index=False, classes='table-zebra', border=0, escape=False)
    
    html_content = f"""
    <style>
        body {{ margin: 0; padding: 0; background-color: #ffffff; color: #1a202c; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        .table-zebra {{ width: 100%; border-collapse: collapse; table-layout: auto; font-size: 14px; color: #1a202c; }}
        .table-zebra tr:nth-of-type(even) {{ background-color: #f7fafc; }}
        .table-zebra tr:nth-of-type(odd) {{ background-color: #ffffff; }}
        .table-zebra th, .table-zebra td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; text-align: left; color: #1a202c; }}
        .table-zebra th:first-child, .table-zebra td:first-child {{ width: 30px; text-align: center; font-weight: bold; }}
        .table-zebra th:nth-child(n+3), .table-zebra td:nth-child(n+3) {{ text-align: center; }}
        .table-zebra th {{ border-bottom: 2px solid #cbd5e0; background-color: #edf2f7; color: #2d3748; font-weight: 600; position: sticky; top: 0; z-index: 1; }}
        .scroll-container {{ max-height: {container_max_height}px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 6px; }}
    </style>
    <div class="scroll-container">{html_table}</div>
    """
    components.html(html_content, height=iframe_height)

def get_rekordy(hledany_limit):
    vsechna_data = []
    
    # Projdeme všechny turnajové soubory
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith(".json"):
            # 1. Datum z názvu
            match = re.search(r'\d{4}-\d{2}-\d{2}', filename)
            datum = match.group(0) if match else "Neznámé"
            
            with open(os.path.join(DATA_FOLDER, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 2. TADY JE TO TŘÍDĚNÍ PODLE TOHO TVÉHO KLÍČE NA KONCI
                if data.get("limit_hodu") == hledany_limit:
                    for team, hraci in data.get("teams", {}).items():
                        for jmeno, body_list in hraci.items():
                            for b in body_list:
                                vsechna_data.append({
                                    "Jméno": jmeno,
                                    "Max": b,
                                    "Datum": datum
                                })
    
    df = pd.DataFrame(vsechna_data)
    if df.empty: return pd.DataFrame(columns=["Jméno", "Max", "Datum"])
    
    # 3. Seřadíme a vezmeme Top 10
    return df.sort_values('Max', ascending=False).head(10)
    


def get_all_tournaments():
    turnaje = []
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            if filename.endswith(".json"):
                filepath = os.path.join(DATA_FOLDER, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
                    if match:
                        year, month, day = match.groups()
                        datum_format = f"{day}. {month}. {year}"
                        sort_key = f"{year}-{month}-{day}"
                    else:
                        datum_format = filename.replace('.json', '')
                        sort_key = filename
                    
                    limit = data.get("limit_hodu", 15)
                    teams = data.get("teams", {})
                    pocet_hracu = sum(len(p) for p in teams.values())
                    pocet_tymu = len(teams)
                    
                    turnaje.append({
                        "filename": filename,
                        "filepath": filepath,
                        "datum_format": datum_format,
                        "sort_key": sort_key,
                        "limit_hodu": limit,
                        "pocet_tymu": pocet_tymu,
                        "pocet_hracu": pocet_hracu,
                        "data": data
                    })
                except Exception:
                    continue
    turnaje.sort(key=lambda x: x["sort_key"], reverse=True)
    return turnaje

def display_tournament_table(df, max_rows=10):
    if df.empty: return
    
    row_count = len(df)
    visible_rows = min(row_count, max_rows)
    container_max_height = 42 + max_rows * 37
    calc_height = 42 + visible_rows * 37 + 10
    iframe_height = min(calc_height, container_max_height + 15)

    html_table = df.to_html(index=False, classes='table-zebra-turnaj', border=0)
    
    html_content = f"""
    <style>
        body {{ margin: 0; padding: 0; background-color: #ffffff; color: #1a202c; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        .table-zebra-turnaj {{ width: 100%; border-collapse: collapse; table-layout: auto; font-size: 14px; color: #1a202c; }}
        .table-zebra-turnaj tr:nth-of-type(even) {{ background-color: #f7fafc; }}
        .table-zebra-turnaj tr:nth-of-type(odd) {{ background-color: #ffffff; }}
        .table-zebra-turnaj th, .table-zebra-turnaj td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; text-align: center; color: #1a202c; }}
        .table-zebra-turnaj th:nth-child(2), .table-zebra-turnaj td:nth-child(2),
        .table-zebra-turnaj th:nth-child(3), .table-zebra-turnaj td:nth-child(3) {{ text-align: left; }}
        .table-zebra-turnaj th:first-child, .table-zebra-turnaj td:first-child {{ width: 35px; text-align: center; font-weight: bold; }}
        .table-zebra-turnaj th {{ border-bottom: 2px solid #cbd5e0; background-color: #edf2f7; color: #2d3748; font-weight: 600; position: sticky; top: 0; z-index: 1; }}
        .scroll-container {{ max-height: {container_max_height}px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 6px; }}
    </style>
    <div class="scroll-container">{html_table}</div>
    """
    components.html(html_content, height=iframe_height)

def vypocitat_pokerove_body(body, umisteni, pocet_hracu):
    return math.sqrt(pocet_hracu) * (body / math.log(umisteni + 1, 2))

def generate_comparison_table(hrac1, hrac2, df_final):
    h1 = df_final[df_final['Jméno'] == hrac1].iloc[0]
    h2 = df_final[df_final['Jméno'] == hrac2].iloc[0]
    
    def format_diff(val, is_lower_better=False, is_percent=False, is_rank=False):
        if is_rank:
            if val < 0:
                return f'<span style="color:#28a745;font-weight:bold;">▲ {abs(val)}</span>'
            elif val > 0:
                return f'<span style="color:#dc3545;font-weight:bold;">▼ {abs(val)}</span>'
            return '<span style="color:#6c757d;">=</span>'
            
        if abs(val) < 1e-5:
            return '<span style="color:#6c757d;">=</span>'
            
        sign = "+" if val > 0 else ""
        color = "#28a745" if (val > 0 if not is_lower_better else val < 0) else "#dc3545"
        suffix = "%" if is_percent else ""
        return f'<span style="color:{color};font-weight:bold;">{sign}{round(val, 2)}{suffix}</span>'

    l1, l2 = h1['Liga'], h2['Liga']
    r1, r2 = int(h1['Liga_Rank']), int(h2['Liga_Rank'])
    b1, b2 = round(h1['Liga Body'] / 10, 1), round(h2['Liga Body'] / 10, 1)
    p1, p2 = round(h1['Průměr na hod'], 2), round(h2['Průměr na hod'], 2)
    rec1, rec2 = int(h1['Max_Kolo']), int(h2['Max_Kolo'])
    t1, t2 = int(h1['Pocet_Turnaju']), int(h2['Pocet_Turnaju'])
    hod1, hod2 = int(h1['Celkem_Hodu']), int(h2['Celkem_Hodu'])
    f1_pct, f2_pct = h1['Forma_Pct'], h2['Forma_Pct']
    
    html = f"""
    <style>
        .comp-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 15px;
            margin-top: 10px;
            margin-bottom: 25px;
        }}
        .comp-table th {{
            background-color: #edf2f7;
            color: #2d3748;
            font-weight: bold;
            padding: 12px;
            border-bottom: 2px solid #cbd5e0;
            text-align: center;
        }}
        .comp-table td {{
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
            text-align: center;
            color: #1a202c;
        }}
        .comp-table tr:hover {{
            background-color: #f7fafc;
        }}
        .metric-name {{
            font-weight: 600;
            text-align: left !important;
            color: #2d3748;
            width: 30%;
        }}
        .winner-cell {{
            background-color: #e6fffa;
            font-weight: bold;
        }}
    </style>
    <table class="comp-table">
        <thead>
            <tr>
                <th style="text-align: left;">Statistika</th>
                <th>👤 {hrac1}</th>
                <th>👥 {hrac2}</th>
                <th>Rozdíl (pro {hrac1})</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="metric-name">🏆 Zařazení (Liga)</td>
                <td>{l1}</td>
                <td>{l2}</td>
                <td>-</td>
            </tr>
            <tr>
                <td class="metric-name">🏅 Pořadí v lize</td>
                <td class="{"winner-cell" if r1 < r2 else ""}">#{r1}</td>
                <td class="{"winner-cell" if r2 < r1 else ""}">#{r2}</td>
                <td>{format_diff(r1 - r2, is_rank=True)}</td>
            </tr>
            <tr>
                <td class="metric-name">⭐ Ligové body</td>
                <td class="{"winner-cell" if b1 > b2 else ""}">{b1} b.</td>
                <td class="{"winner-cell" if b2 > b1 else ""}">{b2} b.</td>
                <td>{format_diff(b1 - b2)} b.</td>
            </tr>
            <tr>
                <td class="metric-name">🎯 Celkový Ø/hod</td>
                <td class="{"winner-cell" if p1 > p2 else ""}">{p1}</td>
                <td class="{"winner-cell" if p2 > p1 else ""}">{p2}</td>
                <td>{format_diff(p1 - p2)}</td>
            </tr>
            <tr>
                <td class="metric-name">🔥 Osobní rekord</td>
                <td class="{"winner-cell" if rec1 > rec2 else ""}">{rec1} b. / kolo</td>
                <td class="{"winner-cell" if rec2 > rec1 else ""}">{rec2} b. / kolo</td>
                <td>{format_diff(rec1 - rec2)} b.</td>
            </tr>
            <tr>
                <td class="metric-name">📈 Aktuální forma</td>
                <td>{round(f1_pct, 1)} %</td>
                <td>{round(f2_pct, 1)} %</td>
                <td>{format_diff(f1_pct - f2_pct)} %</td>
            </tr>
            <tr>
                <td class="metric-name">🎳 Odehrané turnaje (hodů)</td>
                <td>{t1} ({hod1} h.)</td>
                <td>{t2} ({hod2} h.)</td>
                <td>{format_diff(t1 - t2)} turnajů</td>
            </tr>
        </tbody>
    </table>
    """
    return html

def render_player_profile(df_final, df_raw):
    st.markdown("## 👤 Profil hráče a detailní statistiky")
    
    hraci_seznam = sorted(df_final['Jméno'].unique())
    col_sel1, col_sel2, col_sel3 = st.columns([2, 2, 1.5])
    with col_sel1:
        vybrany_hrac = st.selectbox("👤 Vyberte hlavního hráče:", hraci_seznam)
    with col_sel2:
        dalsi_hraci = [h for h in hraci_seznam if h != vybrany_hrac]
        porovnavany_hrac = st.selectbox("⚖️ Porovnat s hráčem (volitelné):", ["-- Vyberte hráče k porovnání --"] + dalsi_hraci)
        if porovnavany_hrac == "-- Vyberte hráče k porovnání --":
            porovnavany_hrac = None
    with col_sel3:
        filtr_hodu = st.selectbox("🎯 Filtr formátu turnaje:", ["Všechny formáty", "10 hodů / kolo", "15 hodů / kolo"])

    hrac_info = df_final[df_final['Jméno'] == vybrany_hrac].iloc[0]
    hrac_raw = df_raw[df_raw['Jméno'] == vybrany_hrac].sort_values('Datum_Sort').copy()
    
    if filtr_hodu == "10 hodů / kolo":
        hrac_filtrovany = hrac_raw[hrac_raw['limit_hodu'] == 10].copy()
    elif filtr_hodu == "15 hodů / kolo":
        hrac_filtrovany = hrac_raw[hrac_raw['limit_hodu'] == 15].copy()
    else:
        hrac_filtrovany = hrac_raw.copy()
        
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.metric("🏆 Zařazení", hrac_info['Liga'], f"#{int(hrac_info['Liga_Rank'])} v lize")
    with m2:
        st.metric("⭐ Ligové body", f"{round(hrac_info['Liga Body'] / 10, 1)} b.")
    with m3:
        st.metric("🎯 Celkový Ø/hod", f"{round(hrac_info['Průměr na hod'], 2)}")
    with m4:
        if hrac_info['Forma_Pct'] >= 5.0:
            st.metric("📈 Aktuální forma", "Rostoucí", f"+{round(hrac_info['Forma_Pct'], 1)} %")
        elif hrac_info['Forma_Pct'] <= -5.0:
            st.metric("📉 Aktuální forma", "Klesající", f"{round(hrac_info['Forma_Pct'], 1)} %")
        else:
            delta_val = f"{round(hrac_info['Forma_Pct'], 1)} %" if hrac_info['Pocet_Turnaju'] >= 2 else "1. turnaj"
            st.metric("📊 Aktuální forma", "Stabilní", delta_val, delta_color="off")
    with m5:
        st.metric("🔥 Osobní rekord", f"{int(hrac_info['Max_Kolo'])} b. / kolo")
    with m6:
        st.metric("🎳 Turnaje", f"{int(hrac_info['Pocet_Turnaju'])} odehráno", f"{int(hrac_info['Celkem_Hodu'])} hodů")
        
    st.markdown("---")

    if hrac_filtrovany.empty:
        st.warning(f"Hráč **{vybrany_hrac}** nemá žádné odehrané turnaje ve formátu {filtr_hodu}.")
        return

    # Pokud porovnáváme, načteme a vyfiltrujeme i druhého hráče
    hrac2_filtrovany = pd.DataFrame()
    if porovnavany_hrac:
        hrac2_raw = df_raw[df_raw['Jméno'] == porovnavany_hrac].sort_values('Datum_Sort').copy()
        if filtr_hodu == "10 hodů / kolo":
            hrac2_filtrovany = hrac2_raw[hrac2_raw['limit_hodu'] == 10].copy()
        elif filtr_hodu == "15 hodů / kolo":
            hrac2_filtrovany = hrac2_raw[hrac2_raw['limit_hodu'] == 15].copy()
        else:
            hrac2_filtrovany = hrac2_raw.copy()
            
        if hrac2_filtrovany.empty:
            st.warning(f"Srovnávaný hráč **{porovnavany_hrac}** nemá žádné odehrané turnaje ve formátu {filtr_hodu}.")

    # Zobrazení tabulky přímého srovnání
    if porovnavany_hrac:
        st.markdown(f"### ⚖️ Přímé srovnání: {vybrany_hrac} vs. {porovnavany_hrac}")
        st.markdown(generate_comparison_table(vybrany_hrac, porovnavany_hrac, df_final), unsafe_allow_html=True)

    graf_data = []
    # Hlavní hráč
    for _, r in hrac_filtrovany.iterrows():
        hody_v_turnaji = len(r['Surove_Body']) * r['limit_hodu']
        avg_turnaj = r['Body'] / hody_v_turnaji if hody_v_turnaji > 0 else 0
        label = f"{r['Datum_Format']} ({r['limit_hodu']}h)"
        graf_data.append({
            "Hráč": vybrany_hrac,
            "Datum": r['Datum_Format'],
            "Datum_Sort": r['Datum_Sort'],
            "Label": label,
            "Limit": f"{r['limit_hodu']} hodů",
            "Body": r['Body'],
            "Průměr na hod": round(avg_turnaj, 2),
            "Umístění": f"{r['Umisteni']}. z {r['Pocet_Hracu']}",
            "Max kolo": max(r['Surove_Body']) if r['Surove_Body'] else 0
        })
        
    # Druhý hráč
    if porovnavany_hrac and not hrac2_filtrovany.empty:
        for _, r in hrac2_filtrovany.iterrows():
            hody_v_turnaji = len(r['Surove_Body']) * r['limit_hodu']
            avg_turnaj = r['Body'] / hody_v_turnaji if hody_v_turnaji > 0 else 0
            label = f"{r['Datum_Format']} ({r['limit_hodu']}h)"
            graf_data.append({
                "Hráč": porovnavany_hrac,
                "Datum": r['Datum_Format'],
                "Datum_Sort": r['Datum_Sort'],
                "Label": label,
                "Limit": f"{r['limit_hodu']} hodů",
                "Body": r['Body'],
                "Průměr na hod": round(avg_turnaj, 2),
                "Umístění": f"{r['Umisteni']}. z {r['Pocet_Hracu']}",
                "Max kolo": max(r['Surove_Body']) if r['Surove_Body'] else 0
            })
    
    df_graf = pd.DataFrame(graf_data)
    if not df_graf.empty:
        df_graf = df_graf.sort_values('Datum_Sort')
    
    if porovnavany_hrac and not hrac2_filtrovany.empty:
        st.markdown("### 📈 Srovnání vývoje průměru na hod")
        fig_prumer = px.line(
            df_graf, 
            x="Label", 
            y="Průměr na hod", 
            color="Hráč",
            markers=True,
            hover_data={"Datum": True, "Průměr na hod": True, "Body": True, "Umístění": True, "Label": False, "Hráč": True},
            title=f"Srovnání vývoje formy"
        )
        fig_prumer.update_traces(line=dict(width=3), marker=dict(size=9))
        fig_prumer.add_hline(y=4.0, line_dash="dash", line_color="green", annotation_text="Hranice Master Ligy (4.0)", annotation_position="bottom right")
        fig_prumer.update_layout(xaxis_title="Turnaj", yaxis_title="Průměr na hod", hovermode="closest", height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_prumer, use_container_width=True)

        st.markdown("### 🎯 Body v jednotlivých kolech")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown(f"##### {vybrany_hrac}")
            kola_data1 = []
            for _, r in hrac_filtrovany.iterrows():
                for k_idx, k_val in enumerate(r['Surove_Body']):
                    kola_data1.append({
                        "Turnaj": f"{r['Datum_Format']} ({r['limit_hodu']}h)",
                        "Kolo": f"{k_idx + 1}. kolo",
                        "Body": k_val
                    })
            df_kola1 = pd.DataFrame(kola_data1)
            fig_kola1 = px.bar(
                df_kola1, 
                x="Turnaj", 
                y="Body", 
                color="Kolo", 
                barmode="group",
                title=f"Náhozy – {vybrany_hrac}",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_kola1.update_layout(xaxis_title="Turnaj", yaxis_title="Počet bodů v kole", height=380, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_kola1, use_container_width=True)
            
        with col_c2:
            st.markdown(f"##### {porovnavany_hrac}")
            kola_data2 = []
            for _, r in hrac2_filtrovany.iterrows():
                for k_idx, k_val in enumerate(r['Surove_Body']):
                    kola_data2.append({
                        "Turnaj": f"{r['Datum_Format']} ({r['limit_hodu']}h)",
                        "Kolo": f"{k_idx + 1}. kolo",
                        "Body": k_val
                    })
            df_kola2 = pd.DataFrame(kola_data2)
            fig_kola2 = px.bar(
                df_kola2, 
                x="Turnaj", 
                y="Body", 
                color="Kolo", 
                barmode="group",
                title=f"Náhozy – {porovnavany_hrac}",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_kola2.update_layout(xaxis_title="Turnaj", yaxis_title="Počet bodů v kole", height=380, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_kola2, use_container_width=True)
            
    else:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("### 📈 Vývoj průměru na hod")
            fig_prumer = px.line(
                df_graf, 
                x="Label", 
                y="Průměr na hod", 
                markers=True,
                hover_data={"Datum": True, "Průměr na hod": True, "Body": True, "Umístění": True, "Label": False},
                title=f"Vývoj formy – {vybrany_hrac}"
            )
            fig_prumer.update_traces(line=dict(color="#1f77b4", width=3), marker=dict(size=9, color="#ff7f0e"))
            fig_prumer.add_hline(y=4.0, line_dash="dash", line_color="green", annotation_text="Hranice Master Ligy (4.0)", annotation_position="bottom right")
            fig_prumer.update_layout(xaxis_title="Turnaj", yaxis_title="Průměr na hod", hovermode="closest", height=380, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_prumer, use_container_width=True)

        with col_g2:
            st.markdown("### 🎯 Body v jednotlivých kolech")
            kola_data = []
            for _, r in hrac_filtrovany.iterrows():
                for k_idx, k_val in enumerate(r['Surove_Body']):
                    kola_data.append({
                        "Turnaj": f"{r['Datum_Format']} ({r['limit_hodu']}h)",
                        "Kolo": f"{k_idx + 1}. kolo",
                        "Body": k_val
                    })
            df_kola = pd.DataFrame(kola_data)
            
            fig_kola = px.bar(
                df_kola, 
                x="Turnaj", 
                y="Body", 
                color="Kolo", 
                barmode="group",
                title=f"Výsledky náhozů – {vybrany_hrac}",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_kola.update_layout(xaxis_title="Turnaj", yaxis_title="Počet bodů v kole", height=380, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_kola, use_container_width=True)

    # Příprava historie turnajů (tabulky)
    hrac_turnaje_rows = []
    max_kol_hrac = max((len(r['Surove_Body']) for _, r in hrac_filtrovany.iterrows()), default=4)
    
    for _, r in hrac_filtrovany.sort_values('Datum_Sort', ascending=False).iterrows():
        rounds = r['Surove_Body']
        hody_t = len(rounds) * r['limit_hodu']
        prum_t = r['Body'] / hody_t if hody_t > 0 else 0
        
        row_t = {
            "Datum": r['Datum_Format'],
            "Formát": f"{r['limit_hodu']} hodů/kolo",
            "Umístění": f"{r['Umisteni']}. / {r['Pocet_Hracu']}"
        }
        for i in range(max_kol_hrac):
            row_t[f"{i+1}."] = rounds[i] if i < len(rounds) else "-"
        row_t["Celkem"] = r['Body']
        row_t["Ø/hod"] = round(prum_t, 2)
        row_t["Max"] = max(rounds) if rounds else 0
        hrac_turnaje_rows.append(row_t)
        
    df_hrac_turnaje = pd.DataFrame(hrac_turnaje_rows)
    if not df_hrac_turnaje.empty:
        df_hrac_turnaje.insert(0, "", range(1, len(df_hrac_turnaje) + 1))

    # Historie druhého hráče
    df_hrac2_turnaje = pd.DataFrame()
    if porovnavany_hrac and not hrac2_filtrovany.empty:
        hrac2_turnaje_rows = []
        max_kol_hrac2 = max((len(r['Surove_Body']) for _, r in hrac2_filtrovany.iterrows()), default=4)
        
        for _, r in hrac2_filtrovany.sort_values('Datum_Sort', ascending=False).iterrows():
            rounds = r['Surove_Body']
            hody_t = len(rounds) * r['limit_hodu']
            prum_t = r['Body'] / hody_t if hody_t > 0 else 0
            
            row_t = {
                "Datum": r['Datum_Format'],
                "Formát": f"{r['limit_hodu']} hodů/kolo",
                "Umístění": f"{r['Umisteni']}. / {r['Pocet_Hracu']}"
            }
            for i in range(max_kol_hrac2):
                row_t[f"{i+1}."] = rounds[i] if i < len(rounds) else "-"
            row_t["Celkem"] = r['Body']
            row_t["Ø/hod"] = round(prum_t, 2)
            row_t["Max"] = max(rounds) if rounds else 0
            hrac2_turnaje_rows.append(row_t)
            
        df_hrac2_turnaje = pd.DataFrame(hrac2_turnaje_rows)
        if not df_hrac2_turnaje.empty:
            df_hrac2_turnaje.insert(0, "", range(1, len(df_hrac2_turnaje) + 1))

    if porovnavany_hrac and not df_hrac2_turnaje.empty:
        st.markdown(f"### 👤 Historie turnajů – {vybrany_hrac}")
        if not df_hrac_turnaje.empty:
            display_tournament_table(df_hrac_turnaje)
        else:
            st.info(f"Hráč {vybrany_hrac} nemá v tomto formátu žádné odehrané turnaje.")
            
        st.markdown(f"### 👥 Historie turnajů – {porovnavany_hrac}")
        display_tournament_table(df_hrac2_turnaje)
    else:
        st.markdown("### 📜 Historie turnajů hráče")
        if not df_hrac_turnaje.empty:
            display_tournament_table(df_hrac_turnaje)
        else:
            st.info("Žádná historie.")

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
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})', file_name)
            if match:
                year, month, day = match.groups()
                datum_format = f"{day}. {month}. {year}"
                datum_sort = f"{year}-{month}-{day}"
            else:
                datum_format = file_name.replace('.json', '')
                datum_sort = file_name
                
            for idx, hrac in enumerate(turnaj_hraci):
                all_stats.append({
                    **hrac, 
                    "Ligove_Body": vypocitat_pokerove_body(hrac['Body'], idx + 1, len(turnaj_hraci)), 
                    "Turnaj": file_name, 
                    "Datum_Sort": datum_sort, 
                    "Datum_Format": datum_format,
                    "limit_hodu": limit_hodu,
                    "Umisteni": idx + 1,
                    "Pocet_Hracu": len(turnaj_hraci)
                })

if all_stats:
    df_raw = pd.DataFrame(all_stats)
    
    def process_player(group):
        vsechny_hody = [h for sublist in group['Surove_Body'] for h in sublist]
        celkem_hodů = sum(len(row['Surove_Body']) * row['limit_hodu'] for _, row in group.iterrows())
        odchylka = np.std(vsechny_hody) if len(vsechny_hody) > 0 else 0
        skokan = 0
        forma = '<span style="color:#6c757d;font-weight:bold;font-size:15px;">▬</span>'
        forma_pct = 0.0
        
        if len(group) >= 2:
            s = group.sort_values('Datum_Sort')
            last_row = s.iloc[-1]
            prev_row = s.iloc[-2]
            
            last_hody = len(last_row['Surove_Body']) * last_row['limit_hodu']
            prev_hody = len(prev_row['Surove_Body']) * prev_row['limit_hodu']
            
            last_avg = last_row['Body'] / last_hody if last_hody > 0 else 0
            prev_avg = prev_row['Body'] / prev_hody if prev_hody > 0 else 0
            
            skokan = max(0, (last_avg - prev_avg) * 2)
            
            if prev_avg > 0:
                rozdil_pct = ((last_avg - prev_avg) / prev_avg) * 100
                forma_pct = rozdil_pct
                if rozdil_pct >= 5.0:
                    forma = '<span style="color:#28a745;font-weight:bold;font-size:16px;">▲</span>'
                elif rozdil_pct <= -5.0:
                    forma = '<span style="color:#dc3545;font-weight:bold;font-size:16px;">▼</span>'
                else:
                    forma = '<span style="color:#6c757d;font-weight:bold;font-size:15px;">▬</span>'
            else:
                forma = '<span style="color:#28a745;font-weight:bold;font-size:16px;">▲</span>' if last_avg > 0 else '<span style="color:#6c757d;font-weight:bold;font-size:15px;">▬</span>'
        
        # Průměr na turnaj, aby čísla nerostla do nekonečna
        prumerne_liga_body = (group['Ligove_Body'].sum() + max(0, (50 - odchylka) / 20) + skokan) / len(group)
        prumer_na_hod = group['Body'].sum() / celkem_hodů if celkem_hodů > 0 else 0
        max_kolo = max((max(row['Surove_Body']) for _, row in group.iterrows() if len(row['Surove_Body']) > 0), default=0)
        
        return pd.Series({
            "Liga Body": prumerne_liga_body, 
            "Průměr na hod": prumer_na_hod,
            "Forma": forma,
            "Forma_Pct": forma_pct,
            "Pocet_Turnaju": len(group),
            "Celkem_Hodu": celkem_hodů,
            "Max_Kolo": max_kolo,
            "Celkem_Bodu": group['Body'].sum()
        })

    df_final = df_raw.groupby('Jméno').apply(process_player, include_groups=False).reset_index()
    df_final['Liga_Rank'] = df_final['Liga Body'].rank(method='min', ascending=False).astype(int)
    df_final['Liga'] = np.where(df_final['Průměr na hod'] > 4.0, "🏆 Master Liga", "🥈 Challenge Liga")

    # Vykreslení aplikace
    logo_path = os.path.join(DATA_FOLDER, "Studio_Galax_1920x1080.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(BASE_DIR, "Historie_turnaju_json", "Studio_Galax_1920x1080.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(BASE_DIR), "Historie_turnaju_json", "Studio_Galax_1920x1080.png")

    qr_path = os.path.join(DATA_FOLDER, "statistiky_qrcode.png")
    if not os.path.exists(qr_path):
        qr_path = os.path.join(BASE_DIR, "Historie_turnaju_json", "statistiky_qrcode.png")

    # Boční panel (Sidebar)
    with st.sidebar:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        st.markdown("### 🎳 Kuželky Liga")
        st.markdown("**Vibe Coder:** Jan Bugdol  \n**Studio:** Studio Galax  \n🤖 **Built with AI:** Claude & Gemini (Cline)")
        st.markdown("📧 [studiogalax.cz@gmail.com](mailto:studiogalax.cz@gmail.com)")
        st.caption("Případné připomínky, nápady na funkce a vylepšení posílejte na e-mail.")
        
        if os.path.exists(qr_path):
            st.markdown("---")
            st.markdown("**📲 Sdílej statistiky:**")
            st.image(qr_path, width=180)
            st.markdown("🔗 [**bit.ly/3SGN1ay**](https://bit.ly/3SGN1ay)")

    st.title("📊 Statistiky kuželkářského turnaje")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Ligová tabulka", "🎯 Průměr na hod", "👤 Profil hráče", "🏆 Top rekordy 10/15", "📜 Historie turnajů", "📖 Pravidla a bodování"])

    with tab1:
        PRUH_LIGY = 4.0
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown("### 🏆 Master Liga")
            display_table(df_final[df_final['Průměr na hod'] > PRUH_LIGY], 'Liga Body', ['Jméno', 'Liga Body', 'Ø/hod', 'Forma'])
        with c2: 
            st.markdown("### 🥈 Challenge Liga")
            display_table(df_final[df_final['Průměr na hod'] <= PRUH_LIGY], 'Liga Body', ['Jméno', 'Liga Body', 'Ø/hod', 'Forma'])

    with tab2:
        c1, _ = st.columns(2)
        with c1:
            st.markdown("### 🎯 Pořadí dle průměru na hod")
            display_table(df_final, 'Průměr na hod', ['Jméno', 'Ø/hod', 'Liga Body', 'Forma'])

    with tab3:
        render_player_profile(df_final, df_raw)

    with tab4:
        # Rozdělíme záložku na dva sloupce
        c1, c2 = st.columns(2)
    
        with c1:
            st.markdown("### 🔥 Top 10 (10 hodů)")
            display_table(get_rekordy(10), 'Max', ['Jméno', 'Max', 'Datum'])
        
        with c2:
            st.markdown("### 🔥 Top 10 (15 hodů)")
            display_table(get_rekordy(15), 'Max', ['Jméno', 'Max', 'Datum'])

    with tab5:
        turnaje = get_all_tournaments()
        if not turnaje:
            st.info("Nebyly nalezeny žádné uložené turnaje.")
        else:
            vybrany_idx = st.selectbox(
                "📅 Vyberte turnaj:",
                options=range(len(turnaje)),
                format_func=lambda i: f"Turnaj ze dne {turnaje[i]['datum_format']} ({turnaje[i]['limit_hodu']} hodů na kolo, {turnaje[i]['pocet_hracu']} hráčů, {turnaje[i]['pocet_tymu']} týmů)"
            )
            
            turnaj = turnaje[vybrany_idx]
            t_data = turnaj["data"]
            limit_h = turnaj["limit_hodu"]
            teams_dict = t_data.get("teams", {})
            
            # Sestavení dat hráčů
            hraci_rows = []
            max_kol = max((len(r) for p in teams_dict.values() for r in p.values()), default=4)
            
            for team_name, players in teams_dict.items():
                for player_name, rounds in players.items():
                    celkem = sum(rounds)
                    hody_celkem = len(rounds) * limit_h
                    prumer_hod = celkem / hody_celkem if hody_celkem > 0 else 0
                    max_kolo = max(rounds) if rounds else 0
                    
                    row = {
                        "Hráč": player_name,
                        "Tým": team_name,
                    }
                    for i in range(max_kol):
                        row[f"{i+1}."] = rounds[i] if i < len(rounds) else "-"
                    row["Celkem"] = celkem
                    row["Ø/hod"] = round(prumer_hod, 2)
                    row["Max"] = max_kolo
                    hraci_rows.append(row)
                    
            df_turnaj_hraci = pd.DataFrame(hraci_rows)
            if not df_turnaj_hraci.empty:
                df_turnaj_hraci = df_turnaj_hraci.sort_values(by=["Celkem", "Max"], ascending=[False, False]).reset_index(drop=True)
                df_turnaj_hraci.insert(0, "", range(1, len(df_turnaj_hraci) + 1))
                
            # Sestavení dat týmů
            tymy_rows = []
            for team_name, players in teams_dict.items():
                team_celkem = sum(sum(rounds) for rounds in players.values())
                p_cnt = len(players)
                team_avg = team_celkem / p_cnt if p_cnt > 0 else 0
                tymy_rows.append({
                    "Tým": team_name,
                    "Celkem": team_celkem,
                    "Počet hráčů": p_cnt,
                    "Ø na hráče": round(team_avg, 1)
                })
            df_turnaj_tymy = pd.DataFrame(tymy_rows)
            if not df_turnaj_tymy.empty:
                df_turnaj_tymy = df_turnaj_tymy.sort_values(by="Celkem", ascending=False).reset_index(drop=True)
                df_turnaj_tymy.insert(0, "", range(1, len(df_turnaj_tymy) + 1))
                
            # Rychlé shrnutí / metriky turnaje
            if not df_turnaj_hraci.empty and not df_turnaj_tymy.empty:
                # 1. Nejvyrovnanější výkon (nejmenší směrodatná odchylka průměru na hod mezi koly)
                stabilita_hraci = []
                for team_name, players in teams_dict.items():
                    for player_name, rounds in players.items():
                        if len(rounds) >= 2:
                            r_avgs = [r / limit_h for r in rounds]
                            std_hod = np.std(r_avgs)
                            std_body = np.std(rounds)
                            stabilita_hraci.append({
                                "Hráč": player_name,
                                "std_hod": std_hod,
                                "std_body": std_body
                            })
                
                if stabilita_hraci:
                    nej_stabilni = min(stabilita_hraci, key=lambda x: x["std_hod"])
                    stabilni_jmeno = nej_stabilni["Hráč"]
                    stabilni_popis = f"±{round(nej_stabilni['std_hod'], 2)} Ø/hod (±{round(nej_stabilni['std_body'], 1)} b.)"
                else:
                    stabilni_jmeno = "—"
                    stabilni_popis = "Nedostatek kol"

                # 2. Skokan turnaje (největší nárůst průměru na hod oproti předchozímu odehranému turnaji)
                skokani = []
                for team_name, players in teams_dict.items():
                    for player_name, rounds in players.items():
                        if rounds:
                            curr_hody = len(rounds) * limit_h
                            curr_avg = sum(rounds) / curr_hody if curr_hody > 0 else 0
                            
                            prev_tourneys = df_raw[(df_raw['Jméno'] == player_name) & (df_raw['Datum_Sort'] < turnaj['sort_key'])].sort_values('Datum_Sort')
                            if not prev_tourneys.empty:
                                prev_row = prev_tourneys.iloc[-1]
                                prev_hody = len(prev_row['Surove_Body']) * prev_row['limit_hodu']
                                prev_avg = prev_row['Body'] / prev_hody if prev_hody > 0 else 0
                                
                                diff_avg = curr_avg - prev_avg
                                pct_diff = ((curr_avg - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0
                                if diff_avg > 0:
                                    skokani.append({
                                        "Hráč": player_name,
                                        "diff_avg": diff_avg,
                                        "pct_diff": pct_diff
                                    })
                
                if skokani:
                    nej_skokan = max(skokani, key=lambda x: x["diff_avg"])
                    skokan_jmeno = nej_skokan["Hráč"]
                    skokan_popis = f"+{round(nej_skokan['diff_avg'], 2)} Ø/hod (+{round(nej_skokan['pct_diff'], 1)}%)"
                else:
                    skokan_jmeno = "—"
                    skokan_popis = "1. turnaj / beze skoku"

                col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
                with col_m1:
                    st.metric("🥇 Vítěz jednotlivců", df_turnaj_hraci.iloc[0]["Hráč"], f"{df_turnaj_hraci.iloc[0]['Celkem']} b.")
                with col_m2:
                    st.metric("🏆 Vítězný tým", df_turnaj_tymy.iloc[0]["Tým"], f"{df_turnaj_tymy.iloc[0]['Celkem']} b.")
                with col_m3:
                    nej_kolo_idx = df_turnaj_hraci["Max"].idxmax()
                    nej_hrac = df_turnaj_hraci.loc[nej_kolo_idx]
                    st.metric("🔥 Nejlepší nához", f"{nej_hrac['Hráč']}", f"{nej_hrac['Max']} b.")
                with col_m4:
                    st.metric("🎯 Nejvyrovnanější hody", stabilni_jmeno, stabilni_popis)
                with col_m5:
                    st.metric("🚀 Skokan turnaje", skokan_jmeno, skokan_popis)
                with col_m6:
                    st.metric("📋 Formát turnaje", f"{limit_h} hodů / kolo", f"{len(df_turnaj_hraci)} hráčů / {len(df_turnaj_tymy)} týmů")
            
            st.markdown("---")
            
            # Zobrazení tabulek jednotlivců a týmů
            col_t1, col_t2 = st.columns([3, 2])
            with col_t1:
                st.markdown("### 👤 Pořadí jednotlivců")
                if not df_turnaj_hraci.empty:
                    display_tournament_table(df_turnaj_hraci)
            with col_t2:
                st.markdown("### 👥 Pořadí týmů")
                if not df_turnaj_tymy.empty:
                    display_tournament_table(df_turnaj_tymy)

    with tab6:
        st.markdown("## 📖 Pravidla ligy, bodování a výpočet statistik")
        st.caption("Kompletní přehled fungování ligy, férového hodnocení a vzorců pro všechny hráče.")
        
        c_p1, c_p2 = st.columns(2)
        
        with c_p1:
            st.markdown("### 🎯 1. Férovost formátů: Průměr na hod (Ø/hod)")
            st.markdown("""
            * Pokud je na turnaji méně hráčů, hraje se **15 hodů na kolo**.
            * Pokud je hráčů více, hraje se **10 hodů na kolo**.
            * **Aby byly výsledky 100% férové a srovnatelné**, veškeré dlouhodobé statistiky, žebříčky a porovnání pracují s **průměrem bodů na 1 hod**:
            $$\\varnothing/\\text{hod} = \\frac{\\text{Celkový počet nahraných bodů}}{\\text{Celkový počet odházených hodů}}$$
            Díky tomu má hodnota $\\varnothing 4.50$ stejnou váhu bez ohledu na to, v jakém formátu byla nahrána.
            """)
            
            st.markdown("---")
            st.markdown("### ⭐ 2. Výpočet Ligových bodů (Turnajový ranking)")
            st.markdown("""
            Ligové body neodráží pouze umístění na bedně, ale zohledňují **sílu konkurence** i **celkový bodový výkon** pomocí osvědčeného rankingového vzorce:
            $$\\text{Body z turnaje} = \\sqrt{N} \\times \\frac{\\text{Nahrané body}}{\\log_2(\\text{Umístění} + 1)}$$
            * $N$ = celkový počet hráčů na daném turnaji *(větší turnaj = větší zisk bodů)*.
            * $\\text{Umístění}$ = pořadí hráče na turnaji *(1. místo získá dělitel 1.0, 2. místo 1.58 atd.)*.
            * **Průměrování na turnaj:** Pro dlouhodobou ligovou tabulku se ligové body dělí počtem odehraných turnajů. Hráči tak nerostou body do nekonečna pouhou účastí, ale rozhoduje **stabilní kvalita výkonů**.
            """)

            st.markdown("---")
            st.markdown("### 🏆 3. Rozdělení do ligových kategorií")
            st.markdown("""
            * 🏆 **Master Liga:** Hráči s celkovým ligovým průměrem **vyšší než 4.00 bodu / hod**.
            * 🥈 **Challenge Liga:** Hráči s celkovým ligovým průměrem **do 4.00 bodu / hod**.
            """)

        with c_p2:
            st.markdown("### ⚖️ 4. Bonus za stabilitu a vyrovnanost hodů")
            st.markdown("""
            Kuželky jsou o přesnosti a stabilitě bez výkyvů.
            * **Směrodatná odchylka ($\\sigma$):** Měří rozptyl bodů mezi jednotlivými náhozy/koly. Čím menší výkyvy hráč má, tím je jeho výkon spolehlivější.
            * **Ligový bonus:** Do celkového hodnocení hráče se přičítá stabilizační bonus:
            $$\\text{Bonus za stabilitu} = \\max\\left(0, \\frac{50 - \\sigma}{20}\\right)$$
            * **🎯 Nejvyrovnanější hody turnaje:** Titul a kartu v *Historii turnajů* získává hráč s nejnižší odchylkou průměru na hod mezi jednotlivými koly turnaje.
            """)

            st.markdown("---")
            st.markdown("### 🚀 5. Skokan turnaje a Forma hráče")
            st.markdown("""
            Oceňujeme progres a růst výkonnosti mezi jednotlivými turnaji:
            * **🚀 Skokan turnaje:** Hráč, který dosáhl největšího zlepšení $\\varnothing/\\text{hod}$ oproti svému předchozímu odehranému turnaji:
            $$\\Delta \\varnothing = \\varnothing_{\\text{aktuální}} - \\varnothing_{\\text{předchozí}}$$
            Hráč za tento skok navíc získává přímý bonus do ligových bodů: $\\text{Bonus} = \\max(0, \\Delta \\varnothing \\times 2)$.  
            *(U prvního turnaje v historii nebo u nováčka se zobrazuje pomlčka, protože chybí srovnávací data).*
            * **📈 Ukazatel formy (v profilu a tabulce):**
              * <span style="color:#28a745;font-weight:bold;">▲ Rostoucí forma:</span> Zlepšení průměru na hod o **+5.0 % a více**.
              * <span style="color:#dc3545;font-weight:bold;">▼ Klesající forma:</span> Pokles průměru na hod o **-5.0 % a více**.
              * <span style="color:#6c757d;font-weight:bold;">▬ Stabilní forma:</span> Výkon v toleranci $\\pm 5.0\\,\\%$.
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 👑 6. Top rekordy (10 a 15 hodů)")
            st.markdown("""
            V síni slávy *Top rekordy* evidujeme historicky nejvyšší náhozy v jednom kole zvlášť pro formát **10 hodů** a zvlášť pro **15 hodů**.
            """)

    # Patička (Footer)
    st.markdown("---")
    col_f1, col_f2 = st.columns([1, 4])
    with col_f1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=160)
    with col_f2:
        st.markdown("""
        🚀 **Vibe Coder:** Jan Bugdol &nbsp;|&nbsp; 🏢 **Studio Galax** &nbsp;|&nbsp; 🤖 **Built with AI:** Claude & Gemini (Cline)  
        📧 **Připomínky, nápady & vylepšení:** [studiogalax.cz@gmail.com](mailto:studiogalax.cz@gmail.com)
        """)

else:
    st.info("Žádná data k zobrazení.")