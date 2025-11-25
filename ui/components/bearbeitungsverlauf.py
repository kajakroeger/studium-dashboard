# ui/components/bearbeitungsverlauf.py
"""
Visualisiert die Bearbeitungszeiten aller abgeschlossenen Kurse als Balkendiagramm.
Zeigt zusätzlich die durchschnittliche Bearbeitungszeit als schwarze Linie.
Entspricht dem Wireframe-Design.
"""

from typing import List, Tuple
from datetime import date, datetime
import streamlit as st
import plotly.graph_objects as go
from .kachel import kachel


def render_bearbeitungsverlauf(service, student_id: int):
    """
    Rendert ein Balkendiagramm mit Bearbeitungszeiten für abgeschlossene Kurse.
    Zusätzlich eine gelbe Verlaufslinie für die durchschnittliche Bearbeitungszeit
    nach jedem abgeschlossenen Kurs.
    """
    with kachel("BEARBEITUNGSVERLAUF"):
        # Bearbeitungszeiten laden
        bearbeitungs_daten = _lade_bearbeitungszeiten(service, student_id)

        if not bearbeitungs_daten:
            st.info(
                "Noch keine abgeschlossenen Kurse vorhanden. "
                "Nach Kursabschluss erscheint hier die Bearbeitungszeit."
            )
            return

        # Daten für Chart vorbereiten
        kursnamen = [kurs_name for kurs_name, _, _ in bearbeitungs_daten]
        bearbeitungszeiten = [tage for _, tage, _ in bearbeitungs_daten]

        # Verlauf der Durchschnittszeiten aus dem Service holen
        verlauf_fn = getattr(service, "verlauf_bearbeitungszeiten", None)
        if callable(verlauf_fn):
            durchschnitts_verlauf = verlauf_fn(student_id) or []
        else:
            durchschnitts_verlauf = []

        # Fallback, falls irgendwas schiefgeht: konstante Durchschnittslinie
        if len(durchschnitts_verlauf) != len(bearbeitungszeiten):
            if bearbeitungszeiten:
                avg = sum(bearbeitungszeiten) / len(bearbeitungszeiten)
                durchschnitts_verlauf = [round(avg, 1)] * len(bearbeitungszeiten)
            else:
                durchschnitts_verlauf = [0.0] * len(bearbeitungszeiten)

        letzter_durchschnitt = (
            durchschnitts_verlauf[-1] if durchschnitts_verlauf else None
        )

        # --- Plotly-Chart ------------------------------------------------------
        fig = go.Figure()

        # Balken: liefern KEIN eigenes Hover, nur Optik
        fig.add_trace(
            go.Bar(
                x=kursnamen,
                y=bearbeitungszeiten,
                name="Bearbeitungszeit",
                marker=dict(
                    color="rgba(6, 182, 212, 0.8)",
                    line=dict(color="rgba(6, 182, 212, 1)", width=1),
                ),
                hoverinfo="skip",  # <- wichtig: kein eigenes Hover
                showlegend=False,
            )
        )

        # customdata: [bearbeitungszeit, durchschnitt_bis_dahin]
        customdata = list(
            zip(bearbeitungszeiten, durchschnitts_verlauf)
        )

        # Verlaufslinie mit kombiniertem Hover
        fig.add_trace(
            go.Scatter(
                x=kursnamen,
                y=durchschnitts_verlauf,
                mode="lines+markers",
                name="Ø Bearbeitungszeit (Verlauf)",
                line=dict(color="rgba(250, 204, 21, 0.9)", width=2, dash="dash"),
                marker=dict(size=6),
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

        # Layout: Hintergrund transparent wie andere Kacheln
        fig.update_layout(
            margin=dict(l=40, r=20, t=20, b=60),
            xaxis_title="Kurs",
            yaxis_title="Bearbeitungszeit in Tagen",
            yaxis=dict(
                gridcolor="rgba(200, 200, 200, 0.2)",
                showgrid=True,
                zeroline=True,
                zerolinecolor="rgba(200, 200, 200, 0.3)",
                tickmode="linear",
                dtick=5,
                range=[0, max(bearbeitungszeiten) * 1.15],
            ),
            xaxis=dict(
                tickangle=-45,
                gridcolor="rgba(200, 200, 200, 0.2)",
                showgrid=False,
                tickfont=dict(size=10),
            ),
            plot_bgcolor="rgba(0,0,0,0)",   # transparent
            paper_bgcolor="rgba(0,0,0,0)",  # transparent
            font=dict(color="white", size=11),
            hovermode="x unified",          # ein gemeinsames Hover-Fenster
            height=300,
            bargap=0.3,

            legend=dict(
                orientation="h",
                yanchor="middle",
                y=1.07,    # Leicht über dem Plot – auf Titelhöhe
                xanchor="right",
                x=0.98,    # Rechtsbündig
                font=dict(color="white", size=11),
            ),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        if letzter_durchschnitt is not None:
            st.caption(f"Ø Bearbeitungszeit (aktuell): {letzter_durchschnitt:.1f} Tage")




def _lade_bearbeitungszeiten(service, student_id: int) -> List[Tuple[str, int, date]]:
    """
    Lädt alle Bearbeitungszeiten für abgeschlossene Kurse.

    Returns:
        Liste von Tupeln: (kurs_kuerzel, bearbeitungszeit_in_tagen, abgabedatum)
        Sortiert nach Abgabedatum.
    """
    bearbeitungs_daten: List[Tuple[str, int, date]] = []

    try:
        bearbeitungen = service.bearbeitungen_fuer_student(student_id) or []

        def to_date(value) -> date | None:
            """Hilfsfunktion: macht aus str/datetime/date ein date-Objekt."""
            if isinstance(value, date) and not isinstance(value, datetime):
                return value
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, str):
                for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
            return None

        for b in bearbeitungen:
            # Status robust als Text holen (Enum oder String)
            raw_status = getattr(b, "status", "")
            status_text = getattr(raw_status, "value", raw_status)
            status_text = str(status_text).strip().lower()

            if status_text != "abgeschlossen":
                continue

            start_raw = getattr(b, "start_datum", None)
            ende_raw = getattr(b, "abgabe_datum", None)
            if not start_raw or not ende_raw:
                continue

            start = to_date(start_raw)
            ende = to_date(ende_raw)
            if not start or not ende:
                continue

            tage = (ende - start).days
            if tage < 0:
                # defensive: falls Daten verdreht sind
                continue

            # Kurs über den öffentlichen Service holen
            kurs_by_id_fn = getattr(service, "kurs_by_id", None)
            kurs = kurs_by_id_fn(b.kurs_id) if callable(kurs_by_id_fn) else None
            if not kurs:
                continue

            kuerzel = getattr(kurs, "kurs_kuerzel", getattr(kurs, "name", ""))
            if len(kuerzel) > 10:
                kurs_display = kuerzel[:7] + "..."
            else:
                kurs_display = kuerzel

            bearbeitungs_daten.append((kurs_display, tage, ende))

    except Exception as e:
        st.error(f"Fehler beim Laden der Bearbeitungszeiten: {e}")

    # nach Abgabedatum sortieren
    bearbeitungs_daten.sort(key=lambda x: x[2])
    return bearbeitungs_daten