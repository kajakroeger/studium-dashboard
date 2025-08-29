import sqlite3, pandas as pd, streamlit as st
from pathlib import Path
import plotly.express as px

DB_PATH = Path("studium.db")
ECTS_ZIEL = 180

def get_con():
    # kurze, robuste Verbindung mit WAL & Timeout
    con = sqlite3.connect(DB_PATH, timeout=10)     # bis zu 10s auf freien Lock warten
    con.execute("PRAGMA busy_timeout=5000")        # zusätzliche Absicherung (5s)
    con.execute("PRAGMA journal_mode=WAL")         # paralleles Lesen bei Schreiben erlauben
    return con

def init_db():
    with get_con() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS kurs(
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ects INTEGER NOT NULL,
                note REAL
            )
        """)

init_db()

# ------------------ Dialog-Trigger ------------------
st.title("📊 Dashboard - Streamlit Test")
if "open_kurs_dialog" not in st.session_state:
    st.session_state.open_kurs_dialog = False

if st.button("➕ Kurs hinzufügen"):
    st.session_state.open_kurs_dialog = True

# ------------------ Dialog-zum Hinzufügen von neuen Kursen ------------------
@st.dialog("Kurs hinzufügen")  
def kurs_dialog():
    with st.form("kurs_form", clear_on_submit=True):
        name = st.text_input("Kursname *")
        ects = st.number_input("ECTS *", min_value=1, step=1, value=5)
        note = st.number_input("Note (optional)", min_value=1.0, max_value=5.0, step=0.1, format="%.1f")

        colA, colB = st.columns(2)
        speichern = colA.form_submit_button("Speichern")
        abbrechen = colB.form_submit_button("Abbrechen", type="secondary")

        if speichern:
            if not name.strip():
                st.error("Bitte einen Kursnamen angeben."); st.stop()
            try:
                # kurze Schreib-Transaktion
                with get_con() as con:
                    con.execute(
                        "INSERT INTO kurs (name, ects, note) VALUES (?,?,?)",
                        (name.strip(), int(ects), float(note) if note else None)
                    )
                st.success("Kurs gespeichert.")
                st.session_state.open_kurs_dialog = False
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Speichern: {e}")

        if abbrechen:
            st.session_state.open_kurs_dialog = False
            st.rerun()

# Dialog anzeigen, wenn getriggert
if st.session_state.open_kurs_dialog:
    kurs_dialog()

st.divider()

# Daten laden (kurz verbinden, dann schließen)
with get_con() as con:
    df_kurs = pd.read_sql_query("SELECT id, name, ects, note FROM kurs ORDER BY id", con)


# --------------------------
# Dashboard-Inhalte
# --------------------------

# --- ECTS-Anzeige --- 
if not df_kurs.empty:
    ects_summe = int(df_kurs["ects"].sum())
    st.metric("ECTS erreicht", f"{ects_summe}/{ECTS_ZIEL}")

# --- Notenverlauf ---
    if df_kurs["note"].notna().any():
        df_plot = df_kurs.copy()
        df_plot["kurzname"] = df_plot["name"].apply(lambda x: " ".join(x.split()[:2]))
        fig = px.line(
            df_plot, x="kurzname", y="note", markers=True,
            title="Notenentwicklung pro Kurs",
            labels={"kurzname": "Kurs", "note": "Note"},
            hover_data=["name"]
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Noch keine Noten hinterlegt – der Notenverlauf erscheint, sobald Kurs-Noten vorhanden sind.")
else:
    st.info("Noch keine Kurse gespeichert.")
