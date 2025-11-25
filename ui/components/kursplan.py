# ui/components/kursplan_gantt.py
from datetime import date, datetime, timedelta
from typing import Optional, List

import streamlit as st
import plotly.graph_objects as go

from .kachel import kachel


def _to_date(value) -> Optional[date]:
    """Hilfsfunktion: str/datetime/date -> date."""
    if value is None:
        return None
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

def _add_months(d: date, months: int) -> date:
    """Hilfsfunktion: fügt einem Datum ganze Monate hinzu."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)  # immer 1. des Monats


def render_kursplan_gantt(service, student_id: int):
    """
    Kursplan: Soll / Ist Vergleich als Gantt-Chart mit Datumsachse.
    - hellblau: geplante Bearbeitungszeit (plan_start -> plan_end)
    - dunkelblau: tatsächliche Bearbeitungszeit (start_datum -> abgabe_datum)
    - x-Achse: echte Daten (Monate), z.B. Apr 2023 – Sept 2023
    """

    with kachel("KURSPLAN: SOLL / IST VERGLEICH"):
        # ---------------------------------------------------------
        # 1) Daten laden und in eine einfache Struktur bringen
        # ---------------------------------------------------------
        bearbeitungen = getattr(
            service, "bearbeitungen_fuer_student", lambda _sid: []
        )(student_id) or []

        rows = []

        for b in bearbeitungen:
            kurs = getattr(service, "kurs_by_id", lambda _id: None)(
                getattr(b, "kurs_id", None)
            )
            if not kurs:
                continue

            semester = getattr(kurs, "semester", None)
            if semester is None:
                # Ohne Semester macht die Gantt-Darstellung wenig Sinn
                continue

            kursname = getattr(kurs, "kurs_kuerzel", None) or getattr(
                kurs, "name", f"Kurs {kurs.id}"
            )

            # Deine vorhandene _to_date-Hilfsfunktion nutzen
            plan_start = _to_date(getattr(b, "plan_start", None))
            plan_end = _to_date(getattr(b, "plan_end", None))
            ist_start = _to_date(getattr(b, "start_datum", None))
            ist_end = _to_date(getattr(b, "abgabe_datum", None))

            # Wenn weder Plan noch Ist irgendwas haben, ignorieren
            if not any([plan_start, plan_end, ist_start, ist_end]):
                continue

            rows.append(
                {
                    "semester": int(semester),
                    "kurs": kursname,
                    "plan_start": plan_start,
                    "plan_end": plan_end,
                    "ist_start": ist_start,
                    "ist_end": ist_end,
                }
            )

        if not rows:
            st.info("Noch keine Kursplanung vorhanden.")
            return

        # ---------------------------------------------------------
        # 2) Semester-Auswahl (Dropdown)
        # ---------------------------------------------------------
        semester_set = sorted({r["semester"] for r in rows})
        sem_label_map = {s: f"{s}. Semester" for s in semester_set}

        col_sem, _ = st.columns([2, 4])
        with col_sem:
            selected_label = st.selectbox(
                "Semester auswählen",
                options=["Alle Semester"] + [sem_label_map[s] for s in semester_set],
                index=0,
            )

        if selected_label == "Alle Semester":
            filtered = rows
        else:
            sel_sem = int(selected_label.split(".")[0])
            filtered = [r for r in rows if r["semester"] == sel_sem]

        if not filtered:
            st.info("Für das gewählte Semester liegen noch keine Daten vor.")
            return

        # ---------------------------------------------------------
        # 3) Figure vorbereiten (Gantt über Scatter-Linien)
        # ---------------------------------------------------------
        fig = go.Figure()

        plan_legend_shown = False
        ist_legend_shown = False

        # sortieren: nach Semester, dann Kursname
        filtered.sort(key=lambda r: (r["semester"], r["kurs"]))

        for r in filtered:
            sem_label = f'{r["semester"]}. Sem'
            kurs_label = f"{sem_label} – {r['kurs']}"

            # Geplanter Zeitraum (hellere Linie)
            if r["plan_start"] and r["plan_end"] and r["plan_end"] >= r["plan_start"]:
                custom = [[r["plan_start"], r["plan_end"]]] * 2
                fig.add_trace(
                    go.Scatter(
                        x=[r["plan_start"], r["plan_end"]],
                        y=[kurs_label, kurs_label],
                        mode="lines",
                        line=dict(
                            color="rgba(59, 130, 246, 0.4)",  # helles Blau
                            width=14,
                        ),
                        name="Geplant",
                        legendgroup="Plan",
                        showlegend=not plan_legend_shown,
                        customdata=custom,
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Typ: Geplant<br>"
                            "Start: %{customdata[0]|%d.%m.%Y}<br>"
                            "Ende: %{customdata[1]|%d.%m.%Y}<extra></extra>"
                        ),
                    )
                )
                plan_legend_shown = True

            # Tatsächlicher Zeitraum (dunklere Linie)
            if r["ist_start"] and r["ist_end"] and r["ist_end"] >= r["ist_start"]:
                custom = [[r["ist_start"], r["ist_end"]]] * 2
                fig.add_trace(
                    go.Scatter(
                        x=[r["ist_start"], r["ist_end"]],
                        y=[kurs_label, kurs_label],
                        mode="lines",
                        line=dict(
                            color="rgba(59, 130, 246, 0.9)",  # dunkles Blau
                            width=8,
                        ),
                        name="Ist",
                        legendgroup="Ist",
                        showlegend=not ist_legend_shown,
                        customdata=custom,
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Typ: Ist<br>"
                            "Start: %{customdata[0]|%d.%m.%Y}<br>"
                            "Ende: %{customdata[1]|%d.%m.%Y}<extra></extra>"
                        ),
                    )
                )
                ist_legend_shown = True

        # ---------------------------------------------------------
        # 4) Heute-Linie auf Datumsachse
        # ---------------------------------------------------------
        heute = date.today()

        fig.add_shape(
            type="line",
            x0=heute,
            x1=heute,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(
                color="rgba(248, 250, 252, 0.8)",
                width=2,
                dash="dash",
            ),
        )

        fig.add_annotation(
            x=heute,
            y=1,
            xref="x",
            yref="paper",
            text="Heute",
            showarrow=False,
            yshift=10,
            font=dict(
                color="rgba(248, 250, 252, 0.9)",
                size=10,
            ),
        )

        # ---------------------------------------------------------
        # 5) x-Achse: Datumsbereich (Semesterlaufzeit)
        # ---------------------------------------------------------
        alle_start = [
            d
            for r in filtered
            for d in (r["plan_start"], r["ist_start"])
            if d is not None
        ]
        alle_end = [
            d
            for r in filtered
            for d in (r["plan_end"], r["ist_end"])
            if d is not None
        ]

        if alle_start and alle_end:
            data_min = min(alle_start)
            data_max = max(alle_end)

            if selected_label == "Alle Semester":
                # --- Studienlaufzeit bestimmen ---

                # Versuche, die aktive Einschreibung zu holen
                eins = getattr(service, "aktive_einschreibung", lambda _sid: None)(student_id)

                studium_start = None
                studium_ende = None

                if eins is not None:
                    studium_start = _to_date(getattr(eins, "start_datum", None))
                    studium_ende = _to_date(getattr(eins, "ziel_enddatum", None))

                # Fallbacks, falls etwas fehlt
                if studium_start is None:
                    studium_start = data_min
                if studium_ende is None:
                    studium_ende = data_max

                # Auf Monatsgrenzen normalisieren
                studium_start = date(studium_start.year, studium_start.month, 1)

                studium_ende_first = date(studium_ende.year, studium_ende.month, 1)
                studium_ende = _add_months(studium_ende_first, 1) - timedelta(days=1)

                min_d = studium_start
                max_d = studium_ende

            else:
                # --- Einzelnes Semester: Semesterfenster + evtl. letzter Abschluss-Monat ---

                sem_start = date(data_min.year, data_min.month, 1)

                # Nominal: 6 Monate Semesterlänge
                sem_end_base_next_month = _add_months(sem_start, 6)
                sem_end_nominal = sem_end_base_next_month - timedelta(days=1)

                last_month_first = date(data_max.year, data_max.month, 1)
                last_month_end = _add_months(last_month_first, 1) - timedelta(days=1)

                sem_end = max(sem_end_nominal, last_month_end)

                min_d = sem_start
                max_d = sem_end

            fig.update_xaxes(range=[min_d, max_d])

        # ---------------------------------------------------------
        # 6) Layout (Dark, Monate auf der x-Achse, Legende oben rechts)
        # ---------------------------------------------------------
        fig.update_xaxes(
            type="date",
            tickformat="%b %y",  # Apr 23, Mai 23, ...
            showgrid=True,
            gridcolor="rgba(107, 114, 128, 0.3)",
            dtick="M1",           # JEDER Monat ein Tick
            ticklabelmode="period",
        )

        fig.update_yaxes(
            automargin=True,
        )

        fig.update_layout(
            margin=dict(l=80, r=20, t=40, b=60),
            xaxis_title="Zeit",
            yaxis_title="Semester / Kurse",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white", size=11),
            hovermode="closest",
            legend=dict(
                orientation="h",
                yanchor="middle",
                y=1.2,
                xanchor="right",
                x=0.98,
                font=dict(color="white"),
            ),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})