import streamlit as st
import pandas as pd
import json
import os
import math
import numpy as np
import streamlit.components.v1 as components
import re

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="Statistiky kuželkářského turnaje", layout="wide")

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

def display_tournament_table(df, height=510):
    if df.empty: return
    
    html_table = df.to_html(index=False, classes='table-zebra-turnaj', border=0)
    
    html_content = f"""
    <style>
        .table-zebra-turnaj {{ width: 100%; border-collapse: collapse; font-family: sans-serif; table-layout: auto; font-size: 14px; }}
        .table-zebra-turnaj tr:nth-of-type(even) {{ background-color: #f0f2f6; }}
        .table-zebra-turnaj th, .table-zebra-turnaj td {{ padding: 8px 10px; border-bottom: 1px solid #eee; white-space: nowrap; text-align: center; }}
        .table-zebra-turnaj th:nth-child(2), .table-zebra-turnaj td:nth-child(2),
        .table-zebra-turnaj th:nth-child(3), .table-zebra-turnaj td:nth-child(3) {{ text-align: left; }}
        .table-zebra-turnaj th:first-child, .table-zebra-turnaj td:first-child {{ width: 35px; text-align: center; font-weight: bold; }}
        .table-zebra-turnaj th {{ border-bottom: 2px solid #ddd; background-color: #ffffff; position: sticky; top: 0; }}
        .scroll-container {{ max-height: {height - 10}px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; }}
    </style>
    <div class="scroll-container">{html_table}</div>
    """
    components.html(html_content, height=height)

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
    
    tab1, tab2, tab3 = st.tabs(["📊 Ligová tabulka", "🏆 Top rekordy 10/15", "📜 Historie turnajů"])

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

    with tab3:
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
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("🥇 Vítěz jednotlivců", df_turnaj_hraci.iloc[0]["Hráč"], f"{df_turnaj_hraci.iloc[0]['Celkem']} b.")
                with col_m2:
                    st.metric("🏆 Vítězný tým", df_turnaj_tymy.iloc[0]["Tým"], f"{df_turnaj_tymy.iloc[0]['Celkem']} b.")
                with col_m3:
                    nej_kolo_idx = df_turnaj_hraci["Max"].idxmax()
                    nej_hrac = df_turnaj_hraci.loc[nej_kolo_idx]
                    st.metric("🔥 Nejlepší nához", f"{nej_hrac['Hráč']}", f"{nej_hrac['Max']} b.")
                with col_m4:
                    st.metric("🎯 Formát turnaje", f"{limit_h} hodů / kolo", f"{len(df_turnaj_hraci)} hráčů / {len(df_turnaj_tymy)} týmů")
            
            st.markdown("---")
            
            # Zobrazení tabulek jednotlivců a týmů
            col_t1, col_t2 = st.columns([3, 2])
            with col_t1:
                st.markdown("### 👤 Pořadí jednotlivců")
                if not df_turnaj_hraci.empty:
                    display_tournament_table(df_turnaj_hraci, height=520)
            with col_t2:
                st.markdown("### 👥 Pořadí týmů")
                if not df_turnaj_tymy.empty:
                    display_tournament_table(df_turnaj_tymy, height=520)

else:
    st.info("Žádná data k zobrazení.")