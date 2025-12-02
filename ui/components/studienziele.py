# ui/components/studienziele.py
"""
Zeigt die Studienziele (Ziel-Abschlussdatum, Ziel-Notenschnitt) an.
"""
import streamlit as st
from .kachel import kachel


def render_studienziele(service, student_id: int):
    """
    Zeigt die Studienziele aus der aktiven Einschreibung an.
    """
    with kachel("STUDIENZIELE"):
        # Aktive Einschreibung holen
        try:
            einschreibung = service.aktive_einschreibung(student_id)
        except Exception:
            einschreibung = None

        if not einschreibung:
            st.info("Keine aktive Einschreibung gefunden.")
            return

        # Ziel-Enddatum
        ziel_enddatum = einschreibung.ziel_enddatum
        if ziel_enddatum:
            st.write(f"Ziel Abschlussdatum: {ziel_enddatum.strftime('%d.%m.%Y')}")
        else:
            st.write("Ziel Abschlussdatum: Nicht hinterlegt")

        # Ziel-Notenschnitt
        ziel_notenschnitt = einschreibung.ziel_notenschnitt
        if ziel_notenschnitt is not None:
            st.write(f"Zielnote mindestens: {ziel_notenschnitt:.2f}")
        else:
            st.write("Zielnote mindestens: Nicht hinterlegt")