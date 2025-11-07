# ui/components/status_overview_tile.py
import streamlit as st
import plotly.graph_objects as go
from .kachel import kachel

def render_status_uebersicht(service, student_id: int, ziel_ects_default: int = 180):
    with kachel("STATUS ÜBERSICHT"):
        # Daten defensiv holen
        try:
            ects_bestanden = float(service.ects_summe_bestanden(student_id) or 0.0)
        except Exception:
            ects_bestanden = 0.0

        try:
            ziele = service.hole_studienziele(student_id)
        except Exception:
            ziele = None

        ziel_ects = (
            getattr(ziele, "ziel_ects", None)
            or getattr(ziele, "ects_ziel", None)
            or ziel_ects_default
        )
        ects_offen = max(ziel_ects - ects_bestanden, 0)

        try:
            avg_grade = service.berechne_notenschnitt(student_id)
        except Exception:
            avg_grade = None

        avg_days_per_5ects = 25  # Placeholder/Beispiel

        c1, c2 = st.columns(2)
        with c1:
            pct = (ects_bestanden / ziel_ects) * 100 if ziel_ects else 0
            fig = _donut(percent=pct, center_text=f"{pct:.0f} %")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption(f"{ects_bestanden:.0f} von {ziel_ects} ECTS erreicht")
        with c2:
            fig2 = _donut(percent=0, center_text=f"{ects_offen:.0f}")
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            st.caption("Noch ECTS offen")

        c3, c4 = st.columns(2)
        with c3:
            st.metric("Ø Note", value="—" if avg_grade is None else f"{avg_grade:.2f}")
        with c4:
            st.metric("Ø Bearbeitungszeit", value=f"{avg_days_per_5ects} Tage", help="pro 5 ECTS (Beispielwert)")

def _donut(percent: float, center_text: str):
    """Kleiner Donut ohne Legende/Textinfos, nur mit Center-Text."""
    return go.Figure(data=[go.Pie(
        values=[percent, max(100 - percent, 0)],
        labels=["", ""],
        hole=0.7,
        textinfo="none",
        hoverinfo="skip"
    )]).update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=[dict(text=center_text, showarrow=False, font=dict(size=20))]
    )
