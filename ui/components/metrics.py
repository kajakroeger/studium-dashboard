"""
ui/components/metrics.py
Kacheln für das Dashboard (oben).
"""
import streamlit as st
from core.dtos import GesamtFortschrittDTO

def render_kpis(overview: GesamtFortschrittDTO) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("ECTS (bestanden)", overview.ects_bestanden)
    col2.metric("ECTS (gesamt bekannt)", overview.ects_gesamt_bekannt)
    col3.metric("ø-Note", "—" if overview.notenschnitt is None else f"{overview.notenschnitt:.2f}")
    col4.metric(
        "Abgeschlossen / Offen",
        f"{overview.anzahl_bearbeitungen_abgeschlossen} / {overview.anzahl_bearbeitungen_offen}",
    )
