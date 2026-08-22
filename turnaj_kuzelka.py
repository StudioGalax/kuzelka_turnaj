import streamlit as st
import pandas as pd
import json
import os
import requests
from datetime import datetime
import os

# 1. DEFINICE CESTY
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_HRACI_PATH = os.path.join(BASE_DIR, "hraci.csv")

def load_hraci_csv():
    if os.path.exists(CSV_HRACI_PATH):
        try:
            df = pd.read_csv(CSV_HRACI_PATH, encoding="utf-8")
            if "ID" in df.columns and "Jméno" in df.columns:
                return df
            elif "Jméno" in df.columns:
                df["ID"] = range(101, 101 + len(df))
                return df
        except Exception:
            pass
    df = pd.DataFrame(columns=["ID", "Jméno"])
    return df

def save_hraci_csv(df):
    df.to_csv(CSV_HRACI_PATH, index=False, encoding="utf-8")

def pridat_hrace_do_csv(nove_jmeno):
    nove_jmeno = str(nove_jmeno).strip()
    if not nove_jmeno:
        return None
    df = load_hraci_csv()
    existing = df[df["Jméno"].str.lower() == nove_jmeno.lower()]
    if not existing.empty:
        return int(existing.iloc[0]["ID"])
    
    if df.empty or df["ID"].isna().all():
        next_id = 101
    else:
        max_id = int(df["ID"].max())
        next_id = max(max_id + 1, 101)
        
    new_row = pd.DataFrame([{"ID": next_id, "Jméno": nove_jmeno}])
    df = pd.concat([df, new_row], ignore_index=True)
    save_hraci_csv(df)
    return next_id

# 2. KONFIGURACE A CSS PRO TISK
st.set_page_config(page_title="Turnaj v kuželkách", layout="wide")

st.markdown("""
    <style>
    table { width: 100% !important; border-collapse: collapse !important; color: black !important; }
    th, td { border: 1px solid #ccc !important; padding: 10px !important; color: black !important; }
    th { background-color: #d3d3d3 !important; font-weight: bold !important; text-align: center !important; }
    tr:nth-child(even) { background-color: #f2f2f2 !important; }
    tr:nth-child(odd) { background-color: #ffffff !important; }

    /* Fix šířky prvního sloupce */
    th:first-child, td:first-child { 
        width: 30px !important; min-width: 30px !important; max-width: 30px !important; 
        text-align: center !important; font-weight: bold !important; 
    }
    td { text-align: left !important; }
    td:nth-child(n+4) { text-align: center !important; }
    
    @media print {
        body, .stApp { background-color: white !important; }
        .stButton, .stDownloadButton, [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stTabs"] { display: block !important; }
        [data-testid="stTab"] { display: block !important; }
    }
    </style>
""", unsafe_allow_html=True)

def uloz_a_resetuj(t, p, idx, score, data):
    data["teams"][t][p][idx] = score
    save_data(data)
    st.session_state["vyber_hraca"] = None

def load_data():
    cesta = get_file_path() # Generuje cestu k souboru pro dnešek
    if os.path.exists(cesta):
        try:
            with open(cesta, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"teams": {}, "tournament_started": False}

def save_data(data):
    cesta = get_file_path() # Generuje cestu k souboru pro dnešek
    with open(cesta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_ngrok_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        data = response.json()
        for tunnel in data.get("tunnels", []):
            if tunnel.get("proto") == "https": return tunnel.get("public_url")
    except: pass
    return "http://localhost:8501"

DATA_DIR = os.path.join(BASE_DIR, "Historie_turnaju_json")
os.makedirs(DATA_DIR, exist_ok=True)

def get_file_path():
    # Získá dnešní datum (nebo včerejší, pokud simuluješ)
    datum_dnes = datetime.now().strftime("%Y-%m-%d")
    nazev = f"turnaj_kuzelka_{datum_dnes}.json"
    return os.path.join(DATA_DIR, nazev)

data = load_data()
is_admin = st.query_params.get("admin") == "yes"

if "vyber_version" not in st.session_state:
    st.session_state["vyber_version"] = 0

st.title("Turnaj v kuželkách")

if is_admin:
    st.sidebar.success("🔑 Režim Rozhodčí")
    url = get_ngrok_url()
    st.sidebar.markdown(f"**Sdílej hráčům:** `{url}`")
    st.sidebar.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={url}")
    
    if not data["tournament_started"]:
        st.header("Registrace týmů")
        limit_hodu = st.radio("Počet hodů na kolo:", [10, 15], horizontal=True)
        
        df_hraci = load_hraci_csv()
        seznam_jmen = sorted(df_hraci["Jméno"].tolist()) if not df_hraci.empty else []
        options_hraci = ["-- Vyber hráče --"] + seznam_jmen + ["➕ [Zadat nového hráče]"]

        st.subheader("➕ Přidat nový tým")
        name = st.text_input("Název týmu:", placeholder="Např. Draci, Devítky...")

        col1, col2 = st.columns(2)
        with col1:
            sel_p1 = st.selectbox("Hráč 1:", options_hraci, key="reg_p1_sel")
            if sel_p1 == "➕ [Zadat nového hráče]":
                p1 = st.text_input("Jméno nového Hráče 1:", key="reg_p1_custom", placeholder="Zadej jméno...").strip()
            elif sel_p1 != "-- Vyber hráče --":
                p1 = sel_p1
            else:
                p1 = ""

            sel_p2 = st.selectbox("Hráč 2:", options_hraci, key="reg_p2_sel")
            if sel_p2 == "➕ [Zadat nového hráče]":
                p2 = st.text_input("Jméno nového Hráče 2:", key="reg_p2_custom", placeholder="Zadej jméno...").strip()
            elif sel_p2 != "-- Vyber hráče --":
                p2 = sel_p2
            else:
                p2 = ""

        with col2:
            sel_p3 = st.selectbox("Hráč 3:", options_hraci, key="reg_p3_sel")
            if sel_p3 == "➕ [Zadat nového hráče]":
                p3 = st.text_input("Jméno nového Hráče 3:", key="reg_p3_custom", placeholder="Zadej jméno...").strip()
            elif sel_p3 != "-- Vyber hráče --":
                p3 = sel_p3
            else:
                p3 = ""

            sel_p4 = st.selectbox("Hráč 4:", options_hraci, key="reg_p4_sel")
            if sel_p4 == "➕ [Zadat nového hráče]":
                p4 = st.text_input("Jméno nového Hráče 4:", key="reg_p4_custom", placeholder="Zadej jméno...").strip()
            elif sel_p4 != "-- Vyber hráče --":
                p4 = sel_p4
            else:
                p4 = ""

        save_new_to_csv = st.checkbox("💾 Automaticky uložit nové hráče do hraci.csv s novým ID (od 101)", value=True)

        if st.button("➕ Přidat tým do turnaje", type="primary"):
            if not name:
                st.error("Vyplňte prosím název týmu.")
            elif not (p1 and p2 and p3 and p4):
                st.error("Vyberte nebo zadejte všechny 4 hráče týmu.")
            elif len({p1, p2, p3, p4}) < 4:
                st.error("Všichni 4 hráči v týmu musí mít unikátní jména.")
            else:
                novi_hraci_zprava = []
                for p in [p1, p2, p3, p4]:
                    if save_new_to_csv:
                        existing_check = df_hraci[df_hraci["Jméno"].str.lower() == p.lower()] if not df_hraci.empty else pd.DataFrame()
                        if existing_check.empty:
                            new_id = pridat_hrace_do_csv(p)
                            novi_hraci_zprava.append(f"{p} (ID: {new_id})")

                data["teams"][name] = {p1: [0,0,0,0], p2: [0,0,0,0], p3: [0,0,0,0], p4: [0,0,0,0]}
                data["limit_hodu"] = limit_hodu
                save_data(data)
                if novi_hraci_zprava:
                    st.success(f"Nové ID přiřazeno: {', '.join(novi_hraci_zprava)}")
                st.rerun()

        if data["teams"]:
            st.markdown("---")
            st.write("📋 **Registrované týmy:**", ", ".join(data["teams"].keys()))
            with st.expander("🛠️ Správa členů týmu"):
                t_name = st.selectbox("Vyber tým pro úpravu", list(data["teams"].keys()))
                if t_name:
                    p_name = st.selectbox("Vyber hráče k odstranění", list(data["teams"][t_name].keys()))
                    if st.button("Odstranit hráče z týmu"):
                        del data["teams"][t_name][p_name]
                        save_data(data)
                        st.rerun()

        with st.expander("👥 Databáze hráčů (hraci.csv) – přehled a správa"):
            df_hraci_curr = load_hraci_csv()
            st.markdown(f"**Uloženo celkem:** `{len(df_hraci_curr)} hráčů`")
            
            c_db1, c_db2 = st.columns([3, 2])
            with c_db1:
                st.dataframe(df_hraci_curr.sort_values("ID"), use_container_width=True, hide_index=True)
            with c_db2:
                st.markdown("##### ➕ Přidat hráče do databáze")
                new_p_name = st.text_input("Jméno hráče:", key="db_new_player_name")
                if st.button("Uložit do hraci.csv"):
                    if new_p_name:
                        nid = pridat_hrace_do_csv(new_p_name)
                        st.success(f"Hráč **{new_p_name}** byl uložen s **ID {nid}**!")
                        st.rerun()
                    else:
                        st.warning("Zadejte jméno hráče.")
                        
                st.markdown("##### 🗑️ Odstranit hráče z databáze")
                if not df_hraci_curr.empty:
                    p_to_del = st.selectbox("Vyber hráče k odstranění:", df_hraci_curr["Jméno"].tolist(), key="db_del_p")
                    if st.button("Smazat z hraci.csv", type="secondary"):
                        df_hraci_curr = df_hraci_curr[df_hraci_curr["Jméno"] != p_to_del]
                        save_hraci_csv(df_hraci_curr)
                        st.success(f"Hráč {p_to_del} byl odstraněn.")
                        st.rerun()

        st.markdown("---")
        if st.button("🚀 ZAHÁJIT TURNAJ", type="primary"):
            if not data["teams"]:
                st.error("Nejprve přidejte alespoň jeden tým.")
            else:
                data["tournament_started"] = True
                save_data(data)
                st.rerun()
    else:
        tab1, tab2, tab3 = st.tabs(["Zápis", "Tabule", "Vyhlášení"])
        with tab1:
            # 1. Příprava seznamu
            hraci_mapa = {}
            vsechni_hraci = []
            for t_name, players in data["teams"].items():
                for p_name in players.keys():
                    oznaceni = f"{p_name} ({t_name})"
                    vsechni_hraci.append(oznaceni)
                    hraci_mapa[oznaceni] = (t_name, p_name)
            
            # 2. Výběr hráče
            vyber = st.selectbox(
            "Vyber hráče:", 
            sorted(vsechni_hraci), 
            key=f"vyber_hraca_{st.session_state['vyber_version']}", # Dynamický klíč
            index=None,
            placeholder="Klikni a piš jméno..."
        )

            # 3. Zápis (pouze pokud je hráč vybraný)
            if vyber:
                t, p = hraci_mapa[vyber]
                hry = data["teams"][t][p]
                    
                if 0 not in hry:
                    st.success(f"✅ Hráč {p} má dohráno!")
                    st.button("Zavřít") # stačí obyčejný button, form zde netřeba
                else:
                    default_game = next((i for i, v in enumerate(hry) if v == 0), 0)
                        
                    with st.form(key=f"zapis_form_{t}_{p}", clear_on_submit=True):
                            idx = st.selectbox("Kolo", range(4), index=default_game, format_func=lambda x: f"{x+1}. kolo")
                            score = st.number_input("Body", min_value=0, value=0)
                            submitted = st.form_submit_button("💾 Uložit")
                        
                    # TADY je to správné místo - tato kontrola se provede jen když existuje formulář
                    if submitted:
                            data["teams"][t][p][idx] = score
                            save_data(data)
                            st.session_state["vyber_version"] += 1
                            st.rerun()

                # 4. Servisní oprava
                with st.expander("🔄 Pokročilá oprava"):
                    oprava_kolo = st.selectbox("Kolo k opravě", range(4), format_func=lambda x: f"{x+1}. kolo", key="edit_kolo")
                    novy_score = st.number_input("Opravené body", min_value=0, value=hry[oprava_kolo], key="edit_score")
                    if st.button("💾 Uložit opravu"):
                        data["teams"][t][p][oprava_kolo] = novy_score
                        save_data(data)
                        st.success("Opraveno!")
                        st.rerun()
            else:
                st.write("Vyber hráče ze seznamu pro zápis bodů.")
        with tab2:
            st.header("Přehled výsledků")
            rows = []
            for t_name, players in data["teams"].items():
                for p_name, hody in players.items():
                    rows.append({"Hráč": p_name, "Tým": t_name, "1.": hody[0], "2.": hody[1], "3.": hody[2], "4.": hody[3], "Celkem": sum(hody)})
            df = pd.DataFrame(rows).sort_values("Celkem", ascending=False).reset_index(drop=True)
            df.insert(0, "Pořadí", range(1, len(df) + 1))
            st.table(df)
        with tab3:
            st.header("Oficiální vyhlášení")
            rows = [{"Pořadí": 0, "Hráč": p, "Tým": t, "Body": sum(d)} for t, ps in data["teams"].items() for p, d in ps.items()]
            df = pd.DataFrame(rows).sort_values("Body", ascending=False).reset_index(drop=True)
            df["Pořadí"] = range(1, len(df) + 1)
            st.subheader("Kompletní pořadí jednotlivců")
            st.table(df)
            worst = df.nsmallest(1, "Body").copy()
            worst["Pořadí"] = "💩"
            st.subheader("Nejslabší jednotlivec")
            st.table(worst)
            df_t = df.groupby("Tým")["Body"].sum().reset_index().sort_values("Body", ascending=False).reset_index(drop=True)
            df_t.insert(0, "Pořadí", range(1, len(df_t) + 1))
            st.subheader("Pořadí všech týmů")
            st.table(df_t)

# --- DIVÁCI ---
else:
    if not data["tournament_started"]:
        st.info("⏰ Turnaj zatím nezačal.")
        st.write("👉 Máte prostor na zkušební hody, systém se spustí po zahájení.")
    else:
        st.header("📊 Průběžné výsledky")
        
        # 1. Příprava dat pro jednotlivce (bez sloupce Tým)
        rows = []
        for t, ps in data["teams"].items():
            for p, h in ps.items():
                rows.append({
                    "Hráč": p, 
                    "1.": h[0], "2.": h[1], "3.": h[2], "4.": h[3], 
                    "Celkem": sum(h)
                })
        
        df_j = pd.DataFrame(rows).sort_values("Celkem", ascending=False).reset_index(drop=True)
        # Prázdný nadpis prvního sloupce (pořadí)
        df_j.insert(0, "", range(1, len(df_j) + 1))
        
        st.subheader("Jednotlivci")
        st.table(df_j)
        
        # 2. Tabulka týmů
        team_totals = []
        for t, ps in data["teams"].items():
            team_score = sum(sum(h) for h in ps.values())
            team_totals.append({"Tým": t, "Celkem": team_score})
            
        df_t = pd.DataFrame(team_totals).sort_values("Celkem", ascending=False).reset_index(drop=True)
        # Týmy pořadí mít mohou, tady to dává smysl
        df_t.insert(0, "Pořadí", range(1, len(df_t) + 1))
        
        st.subheader("Pořadí týmů")
        st.table(df_t)