# ui/components/burndown_chart.py
"""
Burndown Chart: Visualisiert den Fortschritt bei ECTS-Punkten über Zeit.
Zeigt abgeschlossene Kurse als Datenpunkte mit Hover-Informationen.
"""
from datetime import date, timedelta
from typing import List, Tuple, Optional
import streamlit as st
import plotly.graph_objects as go

from models.bearbeitung import StatusBearbeitung
from .kachel import kachel


def render_burndown_chart(service, student_id: int, studiengang_id: Optional[int] = None):
    """
    Rendert ein Burndown Chart, das den Fortschritt bei ECTS-Punkten visualisiert.
    Zeigt abgeschlossene Kurse als Datenpunkte mit Hover-Informationen.
    """
    with kachel("BURN DOWN CHART: ZEITPLAN"):
        # 1) Ziel-ECTS über Studiengang holen
        studiengaenge = service.studiengaenge_by_student_id(student_id)
        
        if not studiengaenge:
            st.info("Kein Studiengang gefunden.")
            return

        studiengang = studiengaenge[0]
        ziel_ects = studiengang.ects_gesamt

        if not ziel_ects or ziel_ects <= 0:
            st.info("Kein ECTS-Ziel im Studiengang hinterlegt.")
            return

        # 2) Einschreibung holen für Start- und Enddatum
        einschreibung = service.aktive_einschreibung(student_id)
        
        if not einschreibung:
            st.info("Keine aktive Einschreibung gefunden.")
            return

        # Startdatum (erster Tag des Monats)
        start_datum = einschreibung.start_datum
        if start_datum:
            start_datum = start_datum.replace(day=1)
        else:
            start_datum = date.today().replace(day=1)

        # Ziel-Enddatum
        ziel_enddatum = einschreibung.ziel_enddatum

        # 3) Abgeschlossene Kurse laden
        abgeschlossene_kurse = _lade_abgeschlossene_kurse(service, student_id)

        # Letztes Abschlussdatum finden
        last_completion_date = None
        if abgeschlossene_kurse:
            last_completion_date = max(k[0] for k in abgeschlossene_kurse)

        # 4) Enddatum bestimmen
        if ziel_enddatum:
            end_datum = ziel_enddatum
        elif last_completion_date:
            # Mindestens bis zum letzten Abschluss + 1 Monat
            tmp = last_completion_date.replace(day=1)
            end_datum = _add_months(tmp, 1)
        else:
            # Fallback: 24 Monate ab Start
            end_datum = _add_months(start_datum, 24)

        # 5) Monatsliste generieren
        months = _generiere_monatsliste(start_datum, end_datum)

        # 6) Ist-Kurve berechnen
        actual_rest, hover_texts, had_flags = _berechne_ist_kurve(
            months,
            ziel_ects,
            abgeschlossene_kurse
        )

        # 7) Ideal-Kurve berechnen (linear)
        total_span = max(len(months) - 1, 1)
        ideal_rest = [
            max(ziel_ects - (ziel_ects * i / total_span), 0)
            for i in range(len(months))
        ]

        # 8) Chart erstellen
        x_labels = [m.strftime("%b %Y") for m in months]
        fig = go.Figure()

        # Ideal-Linie (grau gestrichelt)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=ideal_rest,
            mode="lines",
            name="Ideal",
            line=dict(color='rgba(150, 150, 150, 0.5)', dash='dash'),
            hovertemplate='<b>Ideal</b><br>%{x}<br>Rest-ECTS: %{y:.0f}<extra></extra>',

        ))

        # Ist-Punkte (nur für Monate mit Abschluss)
        x_points = [lbl for lbl, had in zip(x_labels, had_flags) if had]
        y_points = [y for y, had in zip(actual_rest, had_flags) if had]
        hover_points = [t for t, had in zip(hover_texts, had_flags) if had]

        if x_points:  # Nur wenn es Datenpunkte gibt
            fig.add_trace(go.Scatter(
                x=x_points,
                y=y_points,
                mode="lines+markers",
                name="Ist",
                marker=dict(size=8, color='#3b82f6', line=dict(width=2, color='#1e40af')),
                line=dict(color='#3b82f6', width=2),
                hovertemplate='%{text}<extra></extra>',
                text=hover_points
            ))

        # Layout
        fig.update_layout(
            margin=dict(l=40, r=20, t=20, b=60),
            xaxis=dict(
                title="Monat",
                tickangle=-45,
                color="rgba(220,220,220,0.85)",
            ),
            yaxis=dict(
                title="Verbleibende ECTS",
                range=[0, ziel_ects * 1.1],
                dtick=max(ziel_ects // 6, 10),
                color="rgba(220,220,220,0.85)",
                gridcolor="rgba(255,255,255,0.08)",
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=11),
            hovermode='closest',
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

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ==================== Helper-Funktionen ====================

def _add_months(d: date, months: int) -> date:
    """Addiert Monate zu einem Datum."""
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    return date(year, month, 1)


def _lade_abgeschlossene_kurse(service, student_id: int) -> List[Tuple[date, str, int]]:
    """
    Lädt alle abgeschlossenen Kurse mit Abgabedatum, Name und ECTS.

    Returns:
        Liste von Tupeln: (abgabe_datum, kurs_name, ects)
    """
    kurse_mit_daten: List[Tuple[date, str, int]] = []

    try:
        bearbeitungen = service.bearbeitungen_fuer_student(student_id)

        for b in bearbeitungen:
            # Nur abgeschlossene mit Abgabedatum
            if b.status != StatusBearbeitung.ABGESCHLOSSEN:
                continue
            
            if not b.abgabe_datum:
                continue

            # Kurs laden
            kurs = service.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            ects = kurs.ects or 0
            if ects <= 0:
                continue

            kurse_mit_daten.append((b.abgabe_datum, kurs.name, ects))

    except Exception as e:
        st.warning(f"Fehler beim Laden der Kurse: {e}")

    # Nach Abgabedatum sortieren
    kurse_mit_daten.sort(key=lambda x: x[0])
    return kurse_mit_daten


def _generiere_monatsliste(start_d: date, end_d: date) -> List[date]:
    """Generiert eine Liste von Monatsersten zwischen Start- und Enddatum."""
    months: List[date] = []
    cur = start_d
    
    while cur <= end_d:
        months.append(cur)
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1, day=1)
        else:
            cur = cur.replace(month=cur.month + 1, day=1)

    if not months:
        months = [start_d]

    return months


def _berechne_ist_kurve(
    months: List[date],
    ziel_ects: float,
    abgeschlossene_kurse: List[Tuple[date, str, int]]
) -> Tuple[List[float], List[str], List[bool]]:
    """
    Berechnet die Ist-Kurve basierend auf tatsächlichen Abschlüssen.
    
    Returns:
        (actual_rest, hover_texts, had_completion_flags)
    """
    actual_rest: List[float] = []
    hover_texts: List[str] = []
    had_completion_flags: List[bool] = []

    verbleibende_ects = ziel_ects
    kurs_index = 0

    for monat in months:
        monat_str = monat.strftime("%Y-%m")
        kurse_in_monat = []

        # Alle Kurse sammeln, die in diesem Monat abgeschlossen wurden
        while kurs_index < len(abgeschlossene_kurse):
            abgabe_datum, kurs_name, ects = abgeschlossene_kurse[kurs_index]
            abgabe_monat_str = abgabe_datum.strftime("%Y-%m")

            if abgabe_monat_str == monat_str:
                verbleibende_ects -= ects
                kurse_in_monat.append((kurs_name, ects))
                kurs_index += 1
            elif abgabe_monat_str < monat_str:
                # Ältere Abschlüsse nachziehen
                verbleibende_ects -= ects
                kurs_index += 1
            else:
                break

        verbleibende_ects = max(verbleibende_ects, 0)
        actual_rest.append(verbleibende_ects)
        had_completion_flags.append(len(kurse_in_monat) > 0)

        # Hover-Text erstellen
        monat_display = monat.strftime("%b %Y")
        if kurse_in_monat:
            kurse_text = "<br>".join([f"• {name} ({ects} ECTS)" for name, ects in kurse_in_monat])
            hover_texts.append(
                f"<b>{monat_display}</b><br><b>Abgeschlossen:</b><br>{kurse_text}<br>"
                f"<b>Verbleiben noch {verbleibende_ects:.0f} ECTS</b>"
            )
        else:
            hover_texts.append(
                f"<b>{monat_display}</b><br>"
                f"Verbleibende ECTS: {verbleibende_ects:.0f}"
            )

    return actual_rest, hover_texts, had_completion_flags