# ui/components/burndown_chart.py
from datetime import date, timedelta, datetime
from typing import List, Tuple, Optional
import streamlit as st
import plotly.graph_objects as go
from .kachel import kachel


def render_burndown_chart(service, student_id: int, studiengang_id: Optional[int] = None):
    """
    Rendert ein Burndown Chart, das den Fortschritt bei ECTS-Punkten visualisiert.
    Zeigt abgeschlossene Kurse als Datenpunkte mit Hover-Informationen.
    """
    with kachel("BURN DOWN CHART: ZEITPLAN"):
        # ---------------------------------------------------------------------
        # 1) Ziel-ECTS über Studiengang holen (wie in der Status-Kachel)
        # ---------------------------------------------------------------------
        try:
            studiengaenge = service.studiengaenge_fuer_student(student_id) or []
        except Exception:
            studiengaenge = []

        ziel_ects: float
        if studiengaenge:
            # Wenn du später mehrere SGs hast, könntest du hier nach studiengang_id filtern
            akt_sg = studiengaenge[0]
            ziel_ects = float(getattr(akt_sg, "ects_gesamt", 0) or 0)
        else:
            ziel_ects = 0.0

        if ziel_ects <= 0:
            st.info("Kein Studiengang mit ECTS-Ziel gefunden – Burndown-Chart kann nicht sinnvoll dargestellt werden.")
            return

        # ---------------------------------------------------------------------
        # 2) Einschreibungen holen, um den Startmonat festzulegen
        # ---------------------------------------------------------------------
        try:
            eins = service.einschreibungen_fuer_student(student_id) or []
        except Exception:
            eins = []

        start_d: date

        # Versuche: frühestes start_datum aus den Einschreibungen
        start_candidates: List[date] = []
        for e in eins:
            sd = getattr(e, "start_datum", None)
            if isinstance(sd, date):
                start_candidates.append(sd)
            elif isinstance(sd, datetime):
                start_candidates.append(sd.date())

        if start_candidates:
            start_d = min(start_candidates).replace(day=1)
        else:
            # Fallback: heutiger Monat
            start_d = date.today().replace(day=1)

        # Versuche Ziel-Ende aus Einschreibung zu nehmen
        ziel_enddatum = None
        for e in eins:
            ze = getattr(e, "ziel_enddatum", None)
            if isinstance(ze, date):
                ziel_enddatum = ze
                break
            elif isinstance(ze, datetime):
                ziel_enddatum = ze.date()
                break

        # ---------------------------------------------------------------------
        # 3) Abgeschlossene Kurse inkl. Abgabedatum laden
        # ---------------------------------------------------------------------
        abgeschlossene_kurse = _lade_abgeschlossene_kurse(service, student_id)

        # falls es Abschlüsse gibt, Enddatum mind. bis zum letzten Abschluss ziehen
        last_completion_date: Optional[date] = None
        if abgeschlossene_kurse:
            last_completion_date = max(k[0] for k in abgeschlossene_kurse)

        # ---------------------------------------------------------------------
        # 4) Enddatum bestimmen
        # ---------------------------------------------------------------------
        if ziel_enddatum:
            end_d = ziel_enddatum
        elif last_completion_date:
            # mind. bis zum letzten Abschluss, plus ein Monat Puffer
            tmp = last_completion_date.replace(day=1)
            end_d = _add_months(tmp, 1)
        else:
            # sonst einfach 24 Monate ab Start
            end_d = _add_months(start_d, 24)

        # ---------------------------------------------------------------------
        # 5) Monatsliste generieren
        # ---------------------------------------------------------------------
        months = _generiere_monatsliste(start_d, end_d)

        # ---------------------------------------------------------------------
        # 6) Ist-Kurve basierend auf tatsächlichen Abschlüssen berechnen
        # ---------------------------------------------------------------------
        actual_rest, hover_texts, had_flags = _berechne_ist_kurve(
            months,
            ziel_ects,
            abgeschlossene_kurse
        )

        # ---------------------------------------------------------------------
        # 7) Ideal-Kurve: linear von Ziel-ECTS auf 0
        # ---------------------------------------------------------------------
        total_span = max(len(months) - 1, 1)
        ideal_rest = [
            max(ziel_ects - (ziel_ects * i / total_span), 0)
            for i, _ in enumerate(months)
        ]

        # ---------------------------------------------------------------------
        # 8) Chart erstellen
        # ---------------------------------------------------------------------
        x_labels = [m.strftime("%b %Y") for m in months]
        fig = go.Figure()

        # Ideal-Linie
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=ideal_rest,
            mode="lines",
            name="Ideal",
            line=dict(color='rgba(150, 150, 150, 0.5)', dash='dash'),
            hovertemplate='<b>Ideal</b><br>%{x}<br>Rest-ECTS: %{y:.0f}<extra></extra>'
        ))

        # Ist-Punkte NUR für Monate mit Abschluss
        x_points = [lbl for lbl, had in zip(x_labels, had_flags) if had]
        y_points = [y   for y,   had in zip(actual_rest, had_flags) if had]
        hover_points = [t for t,   had in zip(hover_texts, had_flags) if had]

        fig.add_trace(go.Scatter(
            x=x_points,
            y=y_points,
            mode="lines+markers",
            name="Ist",
            marker=dict(size=8, color='#3b82f6', line=dict(width=2, color='#1e40af')),
            hovertemplate='%{text}<extra></extra>',
            text=hover_points
        ))

        # y-Achse: oben beim Ziel-ECTS starten, nach unten Richtung 0
        fig.update_yaxes(
            range=[0, ziel_ects],  # Start oben bei Ziel-ECTS
            title_text="Verbleibende ECTS",
            dtick=max(ziel_ects // 6, 10),
        )

        fig.update_xaxes(title_text="Monat")

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# -------------------------------------------------------------------------
# Helper-Funktionen
# -------------------------------------------------------------------------

def _add_months(d: date, months: int) -> date:
    """Hilfsfunktion, um Monate auf ein Datum zu addieren."""
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
        bearbeitungen = service.bearbeitungen_fuer_student(student_id) or []

        for bearbeitung in bearbeitungen:
            # Status robust als Text holen (Enum ODER String möglich)
            raw_status = getattr(bearbeitung, "status", "")
            status_text = getattr(raw_status, "value", raw_status)
            status_text = str(status_text).strip().lower()

            # Nur abgeschlossene Bearbeitungen mit Abgabedatum
            abgabe_raw = getattr(bearbeitung, "abgabe_datum", None)
            abgabe_datum = _to_date(abgabe_raw)
            if not abgabe_datum:
                continue

            if status_text not in {"abgeschlossen", "eingereicht"}:
                # ggf. hier deine anderen Abschluss-Status ergänzen
                continue

            kurs = service.kurs_by_id(bearbeitung.kurs_id)
            if kurs:
                ects = getattr(kurs, "ects", 0) or 0
                kurse_mit_daten.append(
                    (abgabe_datum, kurs.name, int(ects))
                )
    except Exception as e:
        st.warning(f"Fehler beim Laden der Kurse: {e}")

    # Nach Abgabedatum sortieren
    kurse_mit_daten.sort(key=lambda x: x[0])
    return kurse_mit_daten


def _to_date(value) -> Optional[date]:
    """Hilfsfunktion: wandelt verschiedene Formate in ein date-Objekt um."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y", "%d.%m.%Y %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(text).date()
    except Exception:
        return None


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
        months = [start_d, start_d + timedelta(days=30)]

    return months


def _berechne_ist_kurve(
    months: List[date],
    ziel_ects: float,
    abgeschlossene_kurse: List[Tuple[date, str, int]]
) -> Tuple[List[float], List[str], List[bool]]:
    actual_rest: List[float] = []
    hover_texts: List[str] = []
    had_completion_flags: List[bool] = []

    verbleibende_ects = ziel_ects
    kurs_index = 0

    for monat in months:
        monat_str = monat.strftime("%Y-%m")
        kurse_in_monat = []

        while kurs_index < len(abgeschlossene_kurse):
            abgabe_datum, kurs_name, ects = abgeschlossene_kurse[kurs_index]
            abgabe_monat_str = abgabe_datum.strftime("%Y-%m")

            if abgabe_monat_str == monat_str:
                verbleibende_ects -= ects
                kurse_in_monat.append((kurs_name, ects))
                kurs_index += 1
            elif abgabe_monat_str < monat_str:
                # ältere Abschlüsse nachziehen (falls Startmonat später liegt)
                verbleibende_ects -= ects
                kurs_index += 1
            else:
                break

        verbleibende_ects = max(verbleibende_ects, 0)
        actual_rest.append(verbleibende_ects)
        had_completion_flags.append(len(kurse_in_monat) > 0)

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
