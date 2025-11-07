# ui/components/studienziele_status.py
import streamlit as st
from .kachel import kachel

def render_studienziele_status(service, student_id: int):
    with kachel("AKTUELLER STATUS DER ZIELE"):
        try:
            status = service.berechne_ziel_status(student_id)
        except Exception:
            status = None

        verbleibend = getattr(status, "verbleibende_pruefungen", None) or getattr(status, "remaining_exams", None)
        schnitt_noetig = getattr(status, "schnitt_noetig", None) or getattr(status, "required_avg", None)
        hinweis = getattr(status, "hinweis", None) or getattr(status, "message", None)

        if hinweis:
            st.markdown(f"• {hinweis}")
        if verbleibend is not None:
            st.markdown(f"• Verbleibende Prüfungen: **{verbleibend}**.")
        if schnitt_noetig is not None:
            try:
                st.markdown(f"• Benötigter Schnitt: **{float(schnitt_noetig):.2f}**.")
            except Exception:
                st.markdown(f"• Benötigter Schnitt: **{schnitt_noetig}**.")
        if not any([hinweis, verbleibend is not None, schnitt_noetig is not None]):
            st.caption("Keine Verlaufsdaten vorhanden.")
