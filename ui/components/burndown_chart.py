# ui/components/burndown_chart.py
# Neue Welt ready
"""
Burndown Chart: Visualisiert den Fortschritt bei ECTS-Punkten über Zeit.
Zeigt abgeschlossene Kurse als Datenpunkte mit Hover-Informationen.
"""
import streamlit as st
import plotly.graph_objects as go

from core.view_models import BurndownViewModel
from .kachel import kachel


def render_burndown_chart(vm: BurndownViewModel) -> None:
    """
    Rendert das Burndown Chart auf Basis des BurndownViewModel.
    Keine Service-Aufrufe, keine Domain-Logik mehr.
    """
    with kachel("BURN DOWN CHART: ZEITPLAN"):
        if not vm.hat_daten:
            st.info(vm.fehlermeldung or "Noch keine Daten für das Burndown-Chart.")
            return

        x_labels = vm.monate_labels
        fig = go.Figure()

        # Ideal-Linie
        fig.add_trace(
            go.Scatter(
                x=x_labels,
                y=vm.ideal_verlauf,
                mode="lines",
                name="Ideal",
                line=dict(color="rgba(150, 150, 150, 0.5)", dash="dash"),
                hovertemplate="<b>Ideal</b><br>%{x}<br>Rest-ECTS: %{y:.0f}<extra></extra>",
            )
        )

        # Ist-Punkte (nur Monate mit Abschlüssen)
        x_points = [lbl for lbl, had in zip(x_labels, vm.ist_hat_daten_flags) if had]
        y_points = [y for y, had in zip(vm.ist_verlauf, vm.ist_hat_daten_flags) if had]
        hover_points = [
            t for t, had in zip(vm.ist_hover_texte, vm.ist_hat_daten_flags) if had
        ]

        if x_points:
            fig.add_trace(
                go.Scatter(
                    x=x_points,
                    y=y_points,
                    mode="lines+markers",
                    name="Ist",
                    marker=dict(
                        size=8, color="#3b82f6", line=dict(width=2, color="#1e40af")
                    ),
                    line=dict(color="#3b82f6", width=2),
                    hovertemplate="%{text}<extra></extra>",
                    text=hover_points,
                )
            )

        # Layout
        ziel_ects = vm.ziel_ects or 0
        fig.update_layout(
            margin=dict(l=40, r=20, t=20, b=60),
            xaxis=dict(
                title="Monat",
                tickangle=-45,
                color="rgba(220,220,220,0.85)",
            ),
            yaxis=dict(
                title="Verbleibende ECTS",
                range=[0, max(ziel_ects * 1.1, 10)],
                dtick=max(int(ziel_ects) // 6, 10) if ziel_ects > 0 else 10,
                color="rgba(220,220,220,0.85)",
                gridcolor="rgba(255,255,255,0.08)",
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white", size=11),
            hovermode="closest",
            height=350,
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
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
            key="burndown_chart",
        )


