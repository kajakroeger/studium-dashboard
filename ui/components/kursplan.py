# ui/components/kursplan.py
"""
Kursplan: Soll/Ist-Vergleich als Gantt-Chart mit Datumsachse.
- Hellblau: geplante Bearbeitungszeit (plan_start → plan_end)
- Dunkelblau: tatsächliche Bearbeitungszeit (start_datum → abgabe_datum)
- X-Achse: Echte Datumsachse (Monate)
"""
from datetime import date, timedelta
from typing import Optional
import streamlit as st
import plotly.graph_objects as go

from .kachel import kachel


def render_kursplan_gantt(service, student_id: int, studiengang_id: Optional[int] = None):
    """
    Kursplan: Soll/Ist-Vergleich als Gantt-Chart mit Datumsachse.
    
    Zeigt für jeden Kurs:
    - Geplante Bearbeitungszeit (hellblau, breit)
    - Tatsächliche Bearbeitungszeit (dunkelblau, schmal)
    - Heute-Linie als Orientierung
    """
    with kachel("KURSPLAN: SOLL / IST VERGLEICH"):
        # 1) Daten laden
        bearbeitungen = service.bearbeitungen_fuer_student(student_id)

        rows = []
        for b in bearbeitungen:
            kurs = service.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            semester = kurs.semester
            if semester is None:
                continue  # Ohne Semester keine Darstellung möglich

            kursname = kurs.kurs_kuerzel or kurs.name

            # Datumsfelder sind garantiert date oder None (keine Strings mehr!)
            plan_start = b.plan_start
            plan_end = b.plan_end
            ist_start = b.start_datum
            ist_end = b.abgabe_datum

            # Wenn weder Plan noch Ist vorhanden, überspringen
            if not any([plan_start, plan_end, ist_start, ist_end]):
                continue

            rows.append({
                "semester": int(semester),
                "kurs": kursname,
                "plan_start": plan_start,
                "plan_end": plan_end,
                "ist_start": ist_start,
                "ist_end": ist_end,
            })

        if not rows:
            st.info("Noch keine Kursplanung vorhanden.")
            return

        # 2) Semester-Auswahl (Dropdown)
        semester_set = sorted({r["semester"] for r in rows})
        sem_label_map = {s: f"{s}. Semester" for s in semester_set}

        col_sem, _ = st.columns([2, 4])
        with col_sem:
            selected_label = st.selectbox(
                "Semester auswählen",
                options=["Alle Semester"] + [sem_label_map[s] for s in semester_set],
                index=0,
                key="kursplan_semester_select"
            )

        # Nach Semester filtern
        if selected_label == "Alle Semester":
            filtered = rows
        else:
            sel_sem = int(selected_label.split(".")[0])
            filtered = [r for r in rows if r["semester"] == sel_sem]

        if not filtered:
            st.info("Für das gewählte Semester liegen noch keine Daten vor.")
            return

        # 3) Figure vorbereiten
        fig = go.Figure()

        plan_legend_shown = False
        ist_legend_shown = False

        # Nach Semester und Kursname sortieren
        filtered.sort(key=lambda r: (r["semester"], r["kurs"]))

        for r in filtered:
            sem_label = f'{r["semester"]}. Sem'
            kurs_label = f"{sem_label} – {r['kurs']}"

            # Geplanter Zeitraum (hellblau, breit)
            if r["plan_start"] and r["plan_end"] and r["plan_end"] >= r["plan_start"]:
                fig.add_trace(
                    go.Scatter(
                        x=[r["plan_start"], r["plan_end"]],
                        y=[kurs_label, kurs_label],
                        mode="lines",
                        line=dict(
                            color="rgba(59, 130, 246, 0.4)",  # hellblau
                            width=14,
                        ),
                        name="Geplant",
                        legendgroup="Plan",
                        showlegend=not plan_legend_shown,
                        customdata=[[r["plan_start"], r["plan_end"]]] * 2,
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Typ: Geplant<br>"
                            "Start: %{customdata[0]|%d.%m.%Y}<br>"
                            "Ende: %{customdata[1]|%d.%m.%Y}<extra></extra>"
                        ),
                    )
                )
                plan_legend_shown = True

            # Tatsächlicher Zeitraum (dunkelblau, schmal)
            if r["ist_start"] and r["ist_end"] and r["ist_end"] >= r["ist_start"]:
                fig.add_trace(
                    go.Scatter(
                        x=[r["ist_start"], r["ist_end"]],
                        y=[kurs_label, kurs_label],
                        mode="lines",
                        line=dict(
                            color="rgba(59, 130, 246, 0.9)",  # dunkelblau
                            width=8,
                        ),
                        name="Ist",
                        legendgroup="Ist",
                        showlegend=not ist_legend_shown,
                        customdata=[[r["ist_start"], r["ist_end"]]] * 2,
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Typ: Ist<br>"
                            "Start: %{customdata[0]|%d.%m.%Y}<br>"
                            "Ende: %{customdata[1]|%d.%m.%Y}<extra></extra>"
                        ),
                    )
                )
                ist_legend_shown = True

        # 4) Heute-Linie
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

        # 5) X-Achse: Datumsbereich bestimmen
        alle_start = [
            d for r in filtered
            for d in (r["plan_start"], r["ist_start"])
            if d is not None
        ]
        alle_end = [
            d for r in filtered
            for d in (r["plan_end"], r["ist_end"])
            if d is not None
        ]

        if alle_start and alle_end:
            data_min = min(alle_start)
            data_max = max(alle_end)

            if selected_label == "Alle Semester":
                # Studienlaufzeit aus Einschreibung
                einschreibung = service.aktive_einschreibung(student_id)

                if einschreibung:
                    studium_start = einschreibung.start_datum or data_min
                    studium_ende = einschreibung.ziel_enddatum or data_max
                else:
                    studium_start = data_min
                    studium_ende = data_max

                # Auf Monatsgrenzen normalisieren
                studium_start = date(studium_start.year, studium_start.month, 1)
                studium_ende_first = date(studium_ende.year, studium_ende.month, 1)
                studium_ende = _add_months(studium_ende_first, 1) - timedelta(days=1)

                min_d = studium_start
                max_d = studium_ende

            else:
                # Einzelnes Semester: 6 Monate ab frühestem Datum
                sem_start = date(data_min.year, data_min.month, 1)

                # 6 Monate Semesterlänge
                sem_end_next_month = _add_months(sem_start, 6)
                sem_end_nominal = sem_end_next_month - timedelta(days=1)

                # Letzter Abschluss-Monat
                last_month_first = date(data_max.year, data_max.month, 1)
                last_month_end = _add_months(last_month_first, 1) - timedelta(days=1)

                # Maximum von beiden
                sem_end = max(sem_end_nominal, last_month_end)

                min_d = sem_start
                max_d = sem_end

            fig.update_xaxes(range=[min_d, max_d])

        # 6) Layout
        fig.update_xaxes(
            type="date",
            tickformat="%b %y",  # Apr 23, Mai 23
            showgrid=True,
            gridcolor="rgba(107, 114, 128, 0.3)",
            dtick="M1",  # Jeden Monat ein Tick
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
                font=dict(color="white", size=11),
            ),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ==================== Helper-Funktion ====================

def _add_months(d: date, months: int) -> date:
    """Fügt einem Datum ganze Monate hinzu."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)