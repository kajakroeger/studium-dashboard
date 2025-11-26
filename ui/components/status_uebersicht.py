# ui/components/status_overview_tile.py
import streamlit as st
import plotly.graph_objects as go
from typing import Optional

from .kachel import kachel


def render_status_uebersicht(service, student_id: int, studiengang_id: int):
    with kachel("STATUS ÜBERSICHT"):

        # --- 1) ECTS (bestanden) holen ---
        try:
            ects_bestanden = float(service.ects_summe_bestanden(student_id) or 0.0)
        except Exception:
            ects_bestanden = None

        # --- 2) Ziel-ECTS (ects_gesamt) aus Studiengang holen ---
        try:
            studiengaenge = service.studiengaenge_fuer_student(student_id) or []
        except Exception:
            studiengaenge = []

        if studiengaenge:
            akt_sg = studiengaenge[0]
            ziel_ects = getattr(akt_sg, "ects_gesamt", None)
        else:
            ziel_ects = None

        # --- 3) Ø Note ---
        try:
            avg_grade: Optional[float] = service.berechne_notenschnitt(student_id)
        except Exception:
            avg_grade = None

        # --- 4) Bearbeitungszeit ---
        try:
            avg_days_per_5ects = service.berechne_bearbeitungszeit(student_id)
        except Exception:
            avg_days_per_5ects = None

        # --- 5) ECTS offen ---
        if ziel_ects is not None and ects_bestanden is not None:
            ects_offen = max(ziel_ects - ects_bestanden, 0)
        else:
            ects_offen = None

        # ---------------------------------------------------------------------
        # DONUTS
        # ---------------------------------------------------------------------
        c1, c2 = st.columns(2)

        # Donut 1: Prozent erreicht
        with c1:
            if ziel_ects and ects_bestanden is not None and ziel_ects > 0:
                pct = max(0, min((ects_bestanden / ziel_ects) * 100, 100))
                fig = _donut(percent=pct, center_text=f"{pct:.0f} %")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.caption(f"{ects_bestanden:.0f} von {ziel_ects:.0f} ECTS erreicht")
            else:
                fig = _donut_none()
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.caption("– von – ECTS erreicht")

        # Donut 2: ECTS offen
        with c2:
            if ziel_ects and ects_offen is not None and ziel_ects > 0:
                pct_offen_raw = (ects_offen / ziel_ects) * 100
                pct_offen = max(0, min(pct_offen_raw, 100))
                fig2 = _donut(percent=pct_offen, center_text=f"{ects_offen:.0f}")
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
                st.caption(f"Noch {ects_offen:.0f} ECTS offen")
            else:
                fig2 = _donut_none()
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
                st.caption("Noch – ECTS offen")

        # ---------------------------------------------------------------------
        # METRIKEN
        # ---------------------------------------------------------------------
        c3, c4 = st.columns(2)

        with c3:
            st.metric("Ø Note", value="—" if avg_grade is None else f"{avg_grade:.2f}")

        with c4:
            st.metric(
                "Ø Bearbeitungszeit",
                value="—" if avg_days_per_5ects is None else f"{avg_days_per_5ects:.0f} Tage",
                help="Durchschnittliche Bearbeitungszeit pro 5 ECTS"
            )



def _donut(percent: float, center_text: str):
    """Normaler Donut."""
    fig = go.Figure(
        data=[
            go.Pie(
                values=[percent, max(100 - percent, 0)],
                labels=["", ""],
                hole=0.7,
                textinfo="none",
                hoverinfo="skip",
            )
        ]
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=[dict(text=center_text, showarrow=False, font=dict(size=20))]
    )
    return fig


def _donut_none():
    """Donut für fehlende Daten: grauer Ring + '-' in der Mitte."""
    fig = go.Figure(
        data=[
            go.Pie(
                values=[100],
                labels=[""],
                hole=0.7,
                marker=dict(colors=["#555555"]),
                textinfo="none",
                hoverinfo="skip",
            )
        ]
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=[dict(text="–", showarrow=False, font=dict(size=22, color="#CCCCCC"))]
    )
    return fig
