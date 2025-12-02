# ui/components/bearbeitungsverlauf.py
"""
Visualisiert die Bearbeitungszeiten aller abgeschlossenen Kurse als Balkendiagramm.
Zeigt zusätzlich die durchschnittliche Bearbeitungszeit als gelbe Verlaufslinie.
"""
from typing import List, Tuple
import streamlit as st
import plotly.graph_objects as go

from models.bearbeitung import StatusBearbeitung
from .kachel import kachel


def render_bearbeitungsverlauf(service, student_id: int, studiengang_id: int | None = None):
    """
    Rendert ein Balkendiagramm mit Bearbeitungszeiten für abgeschlossene Kurse.
    Zusätzlich eine gelbe Verlaufslinie für die durchschnittliche Bearbeitungszeit.
    """
    with kachel("BEARBEITUNGSVERLAUF"):
        # 1) Bearbeitungen laden
        bearbeitungen = service.bearbeitungen_fuer_student(student_id)
        
        # 2) Nur abgeschlossene mit Start- und Enddatum
        abgeschlossene = [
            b for b in bearbeitungen
            if b.status == StatusBearbeitung.ABGESCHLOSSEN
            and b.start_datum 
            and b.abgabe_datum
        ]

        if not abgeschlossene:
            st.info("Noch keine abgeschlossenen Kurse vorhanden.")
            return

        # 3) Daten sammeln und sortieren
        bearbeitungs_daten = []
        for b in abgeschlossene:
            kurs = service.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            # Bearbeitungszeit berechnen
            tage = (b.abgabe_datum - b.start_datum).days
            if tage < 0:
                continue  # Fehlerhafte Daten überspringen

            # Kursnamen kürzen falls nötig
            kuerzel = kurs.kurs_kuerzel or kurs.name
            if len(kuerzel) > 10:
                kuerzel = kuerzel[:7] + "..."

            bearbeitungs_daten.append((kuerzel, tage, b.abgabe_datum))

        if not bearbeitungs_daten:
            st.info("Keine gültigen Bearbeitungsdaten vorhanden.")
            return

        # Nach Abgabedatum sortieren
        bearbeitungs_daten.sort(key=lambda x: x[2])

        # 4) Daten für Chart vorbereiten
        kursnamen = [kurs for kurs, _, _ in bearbeitungs_daten]
        bearbeitungszeiten = [tage for _, tage, _ in bearbeitungs_daten]

        # 5) Verlauf der Durchschnittszeiten berechnen
        durchschnitts_verlauf = []
        summe = 0
        for i, tage in enumerate(bearbeitungszeiten, start=1):
            summe += tage
            durchschnitts_verlauf.append(round(summe / i, 1))

        letzter_durchschnitt = durchschnitts_verlauf[-1] if durchschnitts_verlauf else None

        # 6) Plotly-Chart erstellen
        fig = go.Figure()

        # Balken (ohne eigenes Hover)
        fig.add_trace(
            go.Bar(
                x=kursnamen,
                y=bearbeitungszeiten,
                name="Bearbeitungszeit",
                marker=dict(
                    color="rgba(6, 182, 212, 0.8)",
                    line=dict(color="rgba(6, 182, 212, 1)", width=1),
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        # Verlaufslinie mit kombiniertem Hover
        customdata = list(zip(bearbeitungszeiten, durchschnitts_verlauf))
        
        fig.add_trace(
            go.Scatter(
                x=kursnamen,
                y=durchschnitts_verlauf,
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
                showlegend=True,
            )
        )

        # Layout
        fig.update_layout(
            margin=dict(l=40, r=20, t=20, b=60),
            xaxis=dict(
                title="Kurs",
                tickangle=-45,
                gridcolor="rgba(200, 200, 200, 0.2)",
                showgrid=False,
                tickfont=dict(size=10),
            ),
            yaxis=dict(
                title="Bearbeitungszeit in Tagen",
                gridcolor="rgba(200, 200, 200, 0.2)",
                showgrid=True,
                zeroline=True,
                zerolinecolor="rgba(200, 200, 200, 0.3)",
                tickmode="linear",
                dtick=5,
                range=[0, max(bearbeitungszeiten) * 1.15] if bearbeitungszeiten else [0, 10],
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white", size=11),
            hovermode="x unified",
            height=300,
            bargap=0.3,
            legend=dict(
                orientation="h",
                yanchor="middle",
                y=1.07,
                xanchor="right",
                x=0.98,
                font=dict(color="white", size=11),
            ),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Kennzahl anzeigen
        if letzter_durchschnitt is not None:
            st.caption(f"Ø Bearbeitungszeit (aktuell): {letzter_durchschnitt:.1f} Tage")


