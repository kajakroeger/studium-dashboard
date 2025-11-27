# ui/components/goals_tile.py
from datetime import date
import streamlit as st
from .kachel import kachel

def render_studienziele(service, student_id: int):
    with kachel("Studienziele"):
        # Aktive Einschreibung holen (über die Fassade)
        eins = getattr(service, "aktive_einschreibung", lambda _sid: None)(student_id)
        ziel_enddatum = getattr(eins, "ziel_enddatum", None) if eins else None
        st.write("Ziel Abschlussdatum:" , ziel_enddatum or "N/A")

        # Notenschnitt (nur bestandene Prüfungen, laut deiner Logik im Service)
        ziel_notenschnitt = getattr(eins, "ziel_notenschnitt", None)
        st.write(
            "Zielnote mindestens:",
            ziel_notenschnitt if ziel_notenschnitt is not None else "–",
        )