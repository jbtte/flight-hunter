import sqlite3
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd

DB_PATH = "data/flights.db"

st.set_page_config(page_title="Flight Hunter Pro", page_icon="✈️", layout="wide")


def init_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT, route TEXT, price_found REAL, baseline REAL,
            was_pearl INTEGER DEFAULT 0, was_notified INTEGER DEFAULT 0,
            timestamp DATETIME
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_hits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT, message TEXT, is_priority INTEGER DEFAULT 0,
            was_notified INTEGER DEFAULT 0, timestamp DATETIME
        )
    """)
    conn.commit()
    conn.close()

init_tables()


def query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


# ── Header ──────────────────────────────────────────────────────────────────
st.title("✈️ Flight Hunter Pro — Dashboard")

# Status do sistema: último scan
last_scan = query("SELECT MAX(timestamp) as ts FROM scans")
last_ts = last_scan["ts"].iloc[0] if not last_scan.empty else None

if last_ts:
    delta = datetime.now() - datetime.fromisoformat(last_ts)
    horas = delta.total_seconds() / 3600
    if horas < 8:
        st.success(f"Sistema ativo — último scan há {delta.seconds // 3600}h {(delta.seconds % 3600) // 60}min")
    else:
        st.error(f"Sistema pode estar parado — último scan em {last_ts}")
else:
    st.warning("Nenhum scan registrado ainda.")

st.divider()

# ── KPIs ─────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total_scans = query("SELECT COUNT(*) as n FROM scans").iloc[0]["n"]
total_pearls = query("SELECT COUNT(*) as n FROM scans WHERE was_pearl = 1").iloc[0]["n"]
total_notified = query("SELECT COUNT(*) as n FROM scans WHERE was_notified = 1").iloc[0]["n"]
social_hits = query("SELECT COUNT(*) as n FROM social_hits").iloc[0]["n"]

col1.metric("Scans realizados", int(total_scans))
col2.metric("Pérolas encontradas", int(total_pearls))
col3.metric("Alertas enviados", int(total_notified))
col4.metric("Hits sociais", int(social_hits))

st.divider()

# ── Histórico de preços por rota ─────────────────────────────────────────────
st.subheader("Histórico de preços por rota")

rotas = query("SELECT DISTINCT route FROM scans WHERE price_found IS NOT NULL ORDER BY route")
if rotas.empty:
    st.info("Nenhum dado de preço ainda.")
else:
    rota_sel = st.selectbox("Rota", rotas["route"].tolist())

    df_hist = query(
        """
        SELECT timestamp, price_found, baseline, was_pearl, was_notified
        FROM scans
        WHERE route = ? AND price_found IS NOT NULL
        ORDER BY timestamp
        """,
        (rota_sel,),
    )
    df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])

    chart_data = df_hist.set_index("timestamp")[["price_found", "baseline"]].rename(
        columns={"price_found": "Preço encontrado", "baseline": "Baseline"}
    )
    st.line_chart(chart_data)

    # Destaque pérolas
    perolas = df_hist[df_hist["was_pearl"] == 1][["timestamp", "price_found", "baseline", "was_notified"]]
    if not perolas.empty:
        perolas = perolas.rename(columns={
            "timestamp": "Data",
            "price_found": "Preço (R$)",
            "baseline": "Baseline (R$)",
            "was_notified": "Notificado",
        })
        perolas["Notificado"] = perolas["Notificado"].map({1: "Sim", 0: "Não"})
        st.caption(f"💎 {len(perolas)} pérola(s) detectada(s) nessa rota")
        st.dataframe(perolas, use_container_width=True, hide_index=True)

st.divider()

# ── Últimos scans ────────────────────────────────────────────────────────────
st.subheader("Últimos scans")

df_scans = query(
    """
    SELECT timestamp, route, airport, airline, departure_date,
           price_found, baseline, was_pearl, was_notified
    FROM scans ORDER BY timestamp DESC LIMIT 50
    """
)
if not df_scans.empty:
    df_scans["was_pearl"] = df_scans["was_pearl"].map({1: "💎", 0: ""})
    df_scans["was_notified"] = df_scans["was_notified"].map({1: "✅", 0: ""})
    df_scans = df_scans.rename(columns={
        "timestamp": "Scan",
        "route": "Rota",
        "airport": "Aeroporto",
        "airline": "Cia Aérea",
        "departure_date": "Data Ida",
        "price_found": "Preço (R$)",
        "baseline": "Baseline (R$)",
        "was_pearl": "💎",
        "was_notified": "Notif.",
    })
    st.dataframe(df_scans, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum scan ainda.")

st.divider()

# ── Feed social ──────────────────────────────────────────────────────────────
st.subheader("Feed — Social Miner")

dias = st.slider("Últimos N dias", 1, 30, 7)
df_social = query(
    """
    SELECT timestamp, channel, message, is_priority, was_notified
    FROM social_hits
    WHERE timestamp >= ?
    ORDER BY timestamp DESC
    """,
    ((datetime.now() - timedelta(days=dias)).isoformat(),),
)

if df_social.empty:
    st.info("Nenhum hit social nesse período.")
else:
    st.caption(f"{len(df_social)} mensagens capturadas nos últimos {dias} dias")
    for _, row in df_social.iterrows():
        tag = "🚨" if row["is_priority"] else "🎯"
        notif = " · notificado" if row["was_notified"] else ""
        with st.expander(f"{tag} {row['channel']} — {row['timestamp']}{notif}"):
            st.write(row["message"])
