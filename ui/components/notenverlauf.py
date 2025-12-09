# ui/components/notenverlauf.py
"""
Visualisiert den Notenverlauf über alle abgeschlossenen Kurse.
Zeigt die Noten als Linienchart mit Kurskürzel auf der X-Achse.
"""
from typing import List, Tuple
import streamlit as st
import plotly.graph_objects as go

from core.view_models import NotenverlaufViewModel
from models.bearbeitung import StatusBearbeitung
from .kachel import kachel


def render_notenverlauf(vm: NotenverlaufViewModel) -> None:
    """
    Rendert den Notenverlauf inkl. Verlauf des Durchschnitts
    auf Basis des NotenverlaufViewModels.
    """
    with kachel("NOTENVERLAUF"):
        if not vm.hat_daten:
            st.info(vm.fehlermeldung or "Noch keine Noten vorhanden.")
            return

        kursnamen = vm.kursnamen
        noten = vm.noten
        pruefungsformen = vm.pruefungsformen
        running_avgs = vm.durchschnittsverlauf
        overall_avg = vm.durchschnitt if vm.durchschnitt is not None else 0.0
        beste_note = vm.beste_note if vm.beste_note is not None else min(noten)
        anzahl_kurse = vm.anzahl_kurse

        # customdata: [running_avg, pruefungsform]
        customdata = list(zip(running_avgs, pruefungsformen))

        fig = go.Figure()

        # 1) Notenlinie
        fig.add_trace(
            go.Scatter(
                x=kursnamen,
                y=noten,
                mode="lines+markers",
                name="Note",
                line=dict(color="rgba(6, 182, 212, 1)", width=3),
                marker=dict(
                    size=9,
                    color="rgba(6, 182, 212, 1)",
                    line=dict(width=2, color="rgba(255, 255, 255, 1)"),
                ),
                customdata=customdata,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "%{customdata[1]}<br>"
                    "Note: %{y:.1f}<br>"
                    "<extra></extra>"
                ),
                showlegend=True,
            )
        )

        # 2) Verlauf des Durchschnitts
        fig.add_trace(
            go.Scatter(
                x=kursnamen,
                y=running_avgs,
                mode="lines",
                name="Ø-Verlauf",
                line=dict(
                    color="rgba(250, 204, 21, 0.9)", width=2, dash="dash"
                ),
                hovertemplate="Durchschnittsnote: %{y:.2f}<extra></extra>",
                showlegend=True,
            )
        )

        fig.update_layout(
            height=300,
            margin=dict(l=40, r=20, t=20, b=60),
            xaxis=dict(
                title="Kurs",
                tickangle=-45,
                color="rgba(220,220,220,0.85)",
                showgrid=False,
            ),
            yaxis=dict(
                title="Note",
                range=[6.1, 0.9],  # 6.0 unten, 1.0 oben
                autorange=False,
                tickvals=[
                    6.0,
                    5.5,
                    5.0,
                    4.5,
                    4.0,
                    3.5,
                    3.0,
                    2.5,
                    2.0,
                    1.5,
                    1.0,
                ],
                ticktext=[
                    "6,0",
                    "5,5",
                    "5,0",
                    "4,5",
                    "4,0",
                    "3,5",
                    "3,0",
                    "2,5",
                    "2,0",
                    "1,5",
                    "1,0",
                ],
                gridcolor="rgba(255,255,255,0.08)",
                zeroline=False,
                color="rgba(220,220,220,0.85)",
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            hovermode="x unified",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="middle",
                y=1.07,
                xanchor="right",
                x=0.98,
                font=dict(color="white", size=11),
            ),
        )

        st.plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False}
        )

        # Kennzahlen
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Durchschnittsnote", f"{overall_avg:.2f}")
        with col2:
            st.metric("Beste Note", f"{beste_note:.2f}")
        with col3:
            st.metric("Abgeschlossene Kurse", anzahl_kurse)

