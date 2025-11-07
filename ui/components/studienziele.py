# ui/components/goals_tile.py
from datetime import date
import streamlit as st
from .kachel import kachel

def render_studienziele(service, student_id: int):
    with kachel("STUDIENZIELE"):
        try:
            ziele = service.hole_studienziele(student_id)
        except Exception:
            ziele = None

        ziel_schnitt = getattr(ziele, "ziel_notenschnitt", None) or getattr(ziele, "ziel_note", None) or "—"
        try:
            aktueller_schnitt = service.berechne_notenschnitt(student_id)
            aktueller_schnitt = "—" if aktueller_schnitt is None else f"{float(aktueller_schnitt):.2f}"
        except Exception:
            aktueller_schnitt = "—"

        ziel_abschluss = getattr(ziele, "ziel_abschluss", None) or getattr(ziele, "ziel_abschlussdatum", None) or "—"

        st.write(f"**Ziel-Notenschnitt:** {ziel_schnitt} • **aktueller Schnitt:** {aktueller_schnitt}")
        st.write(f"**Ziel-Abschluss:** {ziel_abschluss} • **heute:** {date.today().strftime('%d.%m.%Y')}")
