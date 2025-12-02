# ui/components/notenverlauf.py
"""
Visualisiert den Notenverlauf über alle abgeschlossenen Kurse.
Zeigt die Noten als Linienchart mit Kurskürzel auf der X-Achse.
"""
from typing import List, Tuple
import streamlit as st
import plotly.graph_objects as go

from models.bearbeitung import StatusBearbeitung
from .kachel import kachel


def render_notenverlauf(service, student_id: int, studiengang_id: int | None = None):   
    """
    Rendert den Notenverlauf inkl. Verlauf des Durchschnitts.
    """
    with kachel("NOTENVERLAUF"):
        # Noten-Daten laden
        noten_daten = _lade_noten_mit_kursnamen(service, student_id)

        if not noten_daten:
            st.info(
                "Noch keine Noten vorhanden. "
                "Sobald Kurse abgeschlossen sind, erscheint hier der Notenverlauf."
            )
            return

        # Daten vorbereiten
        kursnamen = [kurs_name for kurs_name, _, _ in noten_daten]
        noten = [note for _, note, _ in noten_daten]
        pruefungsformen = [pf for _, _, pf in noten_daten]

        # Laufender Durchschnitt berechnen
        running_avgs = []
        total = 0.0
        for i, n in enumerate(noten, start=1):
            total += n
            running_avgs.append(total / i)

        overall_avg = running_avgs[-1]

        # customdata: [running_avg, pruefungsform]
        customdata = list(zip(running_avgs, pruefungsformen))

        # Plotly Figure erstellen
        fig = go.Figure()

        # 1) Notenlinie (Türkis)
        fig.add_trace(go.Scatter(
            x=kursnamen,
            y=noten,
            mode='lines+markers',
            name='Note',
            line=dict(color='rgba(6, 182, 212, 1)', width=3),
            marker=dict(
                size=9,
                color='rgba(6, 182, 212, 1)',
                line=dict(width=2, color='rgba(255, 255, 255, 1)')
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{customdata[1]}<br>"
                "Note: %{y:.1f}<br>"
                "<extra></extra>"
            ),
            showlegend=True
        ))

        # 2) Verlauf des Durchschnitts (gestrichelte Linie)
        fig.add_trace(go.Scatter(
            x=kursnamen,
            y=running_avgs,
            mode='lines',
            name='Ø-Verlauf',
            line=dict(color='rgba(250, 204, 21, 0.9)', width=2, dash='dash'),
            hovertemplate="Durchschnittsnote: %{y:.2f}<extra></extra>",
            showlegend=True
        ))

        # Layout
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
                tickvals=[6.0, 5.5, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0],
                ticktext=["6,0", "5,5", "5,0", "4,5", "4,0", "3,5", "3,0", "2,5", "2,0", "1,5", "1,0"],
                gridcolor="rgba(255,255,255,0.08)",
                zeroline=False,
                color="rgba(220,220,220,0.85)",
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            hovermode='x unified',
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

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Kennzahlen
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Durchschnittsnote", f"{overall_avg:.2f}")
        with col2:
            beste_note = min(noten)
            st.metric("Beste Note", f"{beste_note:.2f}")
        with col3:
            anzahl_kurse = len(noten)
            st.metric("Abgeschlossene Kurse", anzahl_kurse)


def _lade_noten_mit_kursnamen(service, student_id: int) -> List[Tuple[str, float, str]]:
    """
    Liefert: [(kurs_display, note, pruefungsform_str), ...]
    """
    noten_daten: List[Tuple[str, float, str]] = []

    try:
        bearbeitungen = service.bearbeitungen_fuer_student(student_id)

        for b in bearbeitungen:
            # Nur abgeschlossene Bearbeitungen mit Abgabedatum
            if b.status != StatusBearbeitung.ABGESCHLOSSEN:
                continue
            if not b.abgabe_datum:
                continue

            # Prüfung über die Fassade holen
            pruefung = service.pruefung_fuer_bearbeitung(b.id)
            if not pruefung:
                continue

            # Nur bestandene Prüfungen mit Note
            if not pruefung.bestanden or pruefung.note is None:
                continue

            pruefungsform_str = (
                pruefung.pruefungsform.value
                if pruefung.pruefungsform
                else "—"
            )

            kurs = service.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            kuerzel = kurs.kurs_kuerzel or kurs.name
            if len(kuerzel) > 20:
                kuerzel = kuerzel[:17] + "..."

            noten_daten.append((kuerzel, float(pruefung.note), pruefungsform_str))

    except Exception as e:
        st.error(f"Fehler beim Laden der Noten: {e}")

    return noten_daten