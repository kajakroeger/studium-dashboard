"""
ui/components/actions.py
Kleine Interaktionen wie "Note eintragen".
"""
import streamlit as st
from core import FortschrittService

def note_eintragen_form(service: FortschrittService) -> None:
    with st.expander("✍️ Note eintragen (Demo)"):
        col1, col2 = st.columns([2, 1])
        bearbeitung_id = col1.number_input("Bearbeitung-ID", min_value=1, step=1)
        note = col2.number_input("Note (z. B. 1.7)", min_value=1.0, max_value=5.0, step=0.1, format="%.1f")
        if st.button("Note speichern"):
            try:
                p = service.trage_note_ein(int(bearbeitung_id), float(note))
                st.success(f"Note gespeichert. Versuch #{p.versuch_nr}, bestanden={p.bestanden}.")
            except Exception as ex:
                st.error(f"Fehler: {ex}")
