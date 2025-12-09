# ui/components/kursplan.py
"""
Kursplan: Soll/Ist-Vergleich als Gantt-Chart mit Datumsachse.
- Hellblau: geplante Bearbeitungszeit (plan_start → plan_end)
- Dunkelblau: tatsächliche Bearbeitungszeit (start_datum → abgabe_datum)
- X-Achse: Echte Datumsachse (Monate)
"""

import streamlit as st
import plotly.graph_objects as go

from core.view_models import KursplanViewModel

from .kachel import kachel


def render_kursplan_gantt(vm: KursplanViewModel) -> None:
    """Rendert den Kursplan (Gantt) auf Basis des KursplanViewModel."""
    with kachel("KURSPLAN"):

        if not vm.hat_daten or not vm.eintraege:
            st.info(vm.fehlermeldung or "Noch keine Daten für den Kursplan.")
            return

        # ---------------------------------------------------------
        # 1) Semester-Auswahl (Dropdown)
        # ---------------------------------------------------------
        eintraege = vm.eintraege  # wird ggf. nach Semester gefiltert

        if vm.semester_optionen:
            # z.B. [1, 2, 3] -> "1. Semester", "2. Semester", ...
            sem_label_map = {
                s: f"{s}. Semester" for s in sorted(vm.semester_optionen)
            }

            col_sem, _ = st.columns([2, 4])
            with col_sem:
                selected_label = st.selectbox(
                    "Semester auswählen",
                    options=["Alle Semester"]
                            + [sem_label_map[s] for s in sorted(vm.semester_optionen)],
                    index=0,
                    key="kursplan_semester_select",
                )

            # Nach Semester filtern
            if selected_label != "Alle Semester":
                sel_sem = int(selected_label.split(".")[0])
                eintraege = [e for e in eintraege if e.semester == sel_sem]

                if not eintraege:
                    st.info("Für das gewählte Semester liegen noch keine Daten vor.")
                    return

        # ---------------------------------------------------------
        # 2) Gantt-Daten mit Scatter-Linien zeichnen
        # ---------------------------------------------------------
        fig = go.Figure()

        # Flags, damit "Plan" / "Ist" nur einmal in der Legende stehen
        first_plan = True
        first_ist = True

        for e in eintraege:
            # ---------- Plan-Spanne ----------
            if e.plan_start and e.plan_end:
                fig.add_trace(
                    go.Scatter(
                        x=[e.plan_start, e.plan_end],
                        y=[e.kurs_label, e.kurs_label],
                        mode="lines",
                        name="Plan",
                        line=dict(
                            width=10,
                            color="rgba(150, 150, 150, 0.6)",
                        ),
                        showlegend=first_plan,
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Plan: %{x[0]|%d.%m.%Y} – %{x[1]|%d.%m.%Y}"
                            "<extra></extra>"
                        ),
                    )
                )
                first_plan = False

            # ---------- Ist-Spanne ----------
            if e.ist_start and e.ist_end:
                fig.add_trace(
                    go.Scatter(
                        x=[e.ist_start, e.ist_end],
                        y=[e.kurs_label, e.kurs_label],
                        mode="lines",
                        name="Ist",
                        line=dict(
                            width=10,
                            color="rgba(37, 99, 235, 0.9)",
                        ),
                        showlegend=first_ist,
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Ist: %{x[0]|%d.%m.%Y} – %{x[1]|%d.%m.%Y}"
                            "<extra></extra>"
                        ),
                    )
                )
                first_ist = False

        fig.update_layout(
            xaxis=dict(
                title="Datum",
                type="date",
                color="rgba(220,220,220,0.85)",
                gridcolor="rgba(255,255,255,0.08)",
            ),
            yaxis=dict(
                title="Kurs",
                automargin=True,
                color="rgba(220,220,220,0.85)",
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white", size=11),
            legend=dict(
                orientation="h",
                yanchor="middle",
                y=1.07,
                xanchor="right",
                x=0.98,
            ),
            margin=dict(l=40, r=20, t=20, b=40),
            height=400,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
            key="kursplan_gantt",
        )