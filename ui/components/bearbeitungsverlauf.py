# ui/components/bearbeitungsverlauf.py
"""

"""
import streamlit as st
import plotly.graph_objects as go

from core.view_models import BearbeitungsverlaufViewModel
from .kachel import kachel


def render_bearbeitungsverlauf(vm: BearbeitungsverlaufViewModel) -> None:
    """
    🥗💁‍♂️ DEKORATEUR 
    - nimmt den fertigen Teller entgegen (ViewModel)
    - serviert ihn optisch ansprechend (Layout + Visualisierung)
    - visualisiert die Bearbeitungszeit je abgeschlossenen Kurs und den Verlauf der 
      durchschnittlichen Bearbeitungszeit.

    Technisch:
    - arbeitet ausschließlich mit ViewModels (keine DTOs, keine Models)
    - enthält keine Service-Aufrufe (kein WorkflowService/ProgressService)
    - enthält keine Geschäftslogik (keine ECTS-/Noten-Berechnungen)
    - stellt dar:
        - Streamlit-Widgets
        - Plotly-Figure bauen
        - Styling, Achsen, Hover, Leerezustände anzeigen
    """
    with kachel("BEARBEITUNGSVERLAUF"):
        if not vm.hat_daten or not vm.eintraege:
            st.info(vm.fehlermeldung or "Noch keine Bearbeitungen vorhanden.")
            return

        # Nur Einträge mit gültiger Dauer für das Diagramm
        eintraege = [e for e in vm.eintraege if e.dauer_tage is not None]
        if not eintraege:
            st.info("Keine gültigen Bearbeitungsdaten vorhanden.")
            return

        labels = [e.kurs_label for e in eintraege]
        dauer = [int(e.dauer_tage) for e in eintraege]

        fig = go.Figure()

        # Balken
        fig.add_trace(
            go.Bar(
                x=labels,
                y=dauer,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Dauer: %{y} Tage<extra></extra>"
                ),
                name="Bearbeitungszeit",
            )
        )

        # Verlauf der durchschnittlichen Bearbeitungszeit
        if vm.durchschnitt_verlauf:
            verlauf = vm.durchschnitt_verlauf

            # Sicherheitscheck: Länge angleichen
            n = min(len(verlauf), len(dauer))
            verlauf = verlauf[:n]
            labels = labels[:n]
            dauer = dauer[:n]

            avg_values = [round(p["avg_dauer_tage"], 1) for p in verlauf]
            customdata = list(zip(dauer, avg_values))

            fig.add_trace(
                go.Scatter(
                    x=labels,
                    y=avg_values,
                    mode="lines+markers",
                    name="Ø Bearbeitungszeit (Verlauf)",
                    line=dict(color="rgba(250, 204, 21, 0.9)", width=2, dash="dash"),
                    marker=dict(size=6, color="rgba(250, 204, 21, 1)"),
                    customdata=customdata,
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Bearbeitungszeit: %{customdata[0]} Tage<br>"
                        "Ø bis dahin: %{customdata[1]} Tage"
                        "<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            xaxis=dict(
                title="Kurs",
                tickangle=-45,
                color="rgba(220,220,220,0.85)",
            ),
            yaxis=dict(
                title="Bearbeitungszeit in Tagen",
                color="rgba(220,220,220,0.85)",
                gridcolor="rgba(255,255,255,0.08)",
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white", size=11),
            margin=dict(l=40, r=20, t=20, b=80),
            height=350,
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
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
            key="bearbeitungsverlauf",
        )

        # Kennzahl unten anzeigen
        if vm.durchschnitt is not None:
            st.caption(f"Ø Bearbeitungszeit (aktuell): {vm.durchschnitt:.1f} Tage")



