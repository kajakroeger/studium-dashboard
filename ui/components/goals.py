"""
ui/components/goals.py
Zweite Dashboard-Zeile: Studienziele & aktueller Ziel-Status.
"""
import streamlit as st
from core import FortschrittService

def render_goals_row(service: FortschrittService, student_id: int) -> None:
    ziele = service.hole_studienziele(student_id)
    status = service.berechne_ziel_status(student_id)

    col1, col2 = st.columns(2)

    # --- Kachel 1: Studienziele ---
    with col1:
        st.markdown("**STUDIENZIELE**")
        st.write(
            f"**Ziel-Notenschnitt:** "
            f"{'—' if ziele.ziel_notenschnitt is None else f'{ziele.ziel_notenschnitt:.2f}'}   "
            f"• **aktueller Schnitt:** "
            f"{'—' if ziele.aktueller_notenschnitt is None else f'{ziele.aktueller_notenschnitt:.2f}'}"
        )
        st.write(
            f"**Ziel-Abschluss:** "
            f"{'—' if ziele.ziel_enddatum is None else ziele.ziel_enddatum.strftime('%d.%m.%Y')}   "
            f"• **heute:** {ziele.heutiges_datum.strftime('%d.%m.%Y')}"
        )

    # --- Kachel 2: Aktueller Status der Ziele ---
    with col2:
        st.markdown("**AKTUELLER STATUS DER ZIELE**")
        # Noten-Kommentar
        st.write("• " + status.kommentar_note)
        # Zeit-Kommentar
        st.write("• " + status.kommentar_zeit)
