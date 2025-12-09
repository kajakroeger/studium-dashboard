# ui/components/status_uebersicht.py
# neue Welt ready
import streamlit as st
import plotly.graph_objects as go
from typing import Optional

from core.view_models import StatusUebersichtViewModel
from .kachel import kachel


def render_status_uebersicht(vm: StatusUebersichtViewModel) -> None:
    """Rendert die Status-Übersicht Kachel auf Basis des ViewModels."""
    with kachel("STATUS ÜBERSICHT"):

        ziel_ects = vm.ects_ziel
        ects_bestanden = vm.ects_bestanden
        ects_offen = vm.ects_offen
        avg_grade = vm.notenschnitt
        avg_days_per_5ects = vm.bearbeitungszeit_pro_5ects

        # -----------------------------------------------------------------
        # DONUTS
        # -----------------------------------------------------------------
        c1, c2 = st.columns(2)

        # Donut 1: Prozent erreicht
        with c1:
            if ziel_ects and ects_bestanden is not None and ziel_ects > 0:
                pct = max(0.0, min((ects_bestanden / ziel_ects) * 100.0, 100.0))
                fig = _donut(percent=pct, center_text=f"{pct:.0f} %")
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key="donut_erreicht",
                )
                st.caption(f"{ects_bestanden:.0f} von {ziel_ects:.0f} ECTS erreicht")
            else:
                fig = _donut_none()
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key="donut_erreicht_leer",
                )
                st.caption("– von – ECTS erreicht")

        # Donut 2: ECTS offen
        with c2:
            if ziel_ects and ects_offen is not None and ziel_ects > 0:
                pct_offen = max(0.0, min((ects_offen / ziel_ects) * 100.0, 100.0))
                fig2 = _donut(percent=pct_offen, center_text=f"{ects_offen:.0f}")
                st.plotly_chart(
                    fig2,
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key="donut_offen",
                )
                st.caption(f"Noch {ects_offen:.0f} ECTS offen")
            else:
                fig2 = _donut_none()
                st.plotly_chart(
                    fig2,
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key="donut_offen_leer",
                )
                st.caption("Noch – ECTS offen")

        # -----------------------------------------------------------------
        # METRIKEN
        # -----------------------------------------------------------------
        c3, c4 = st.columns(2)

        with c3:
            st.metric(
                "Ø Note",
                value="—" if avg_grade is None else f"{avg_grade:.2f}",
            )

        with c4:
            st.metric(
                "Ø Bearbeitungszeit",
                value="—" if avg_days_per_5ects is None else f"{avg_days_per_5ects:.0f} Tage",
                help="Durchschnittliche Bearbeitungszeit pro 5 ECTS",
            )



def _donut(percent: float, center_text: str) -> go.Figure:
    """
    Erstellt einen Donut-Chart.
    
    Args:
        percent: Prozentsatz (0-100)
        center_text: Text in der Mitte
    
    Returns:
        Plotly Figure
    """
    fig = go.Figure(
        data=[
            go.Pie(
                values=[percent, max(100 - percent, 0)],
                labels=["", ""],
                hole=0.7,
                textinfo="none",
                hoverinfo="skip",
                marker=dict(colors=["#3b82f6", "#1e293b"]),  # Blau + Dunkelgrau
            )
        ]
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=[
            dict(
                text=center_text,
                showarrow=False,
                font=dict(size=20, color="white")
            )
        ],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _donut_none() -> go.Figure:
    """
    Donut für fehlende Daten: grauer Ring + '—' in der Mitte.
    
    Returns:
        Plotly Figure
    """
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
        annotations=[
            dict(
                text="—",
                showarrow=False,
                font=dict(size=22, color="#CCCCCC")
            )
        ],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig