# ui/components/burndown_chart.py
from datetime import date, timedelta
import streamlit as st
import plotly.graph_objects as go
from .kachel import kachel

def render_burndown_chart(service, student_id: int, ziel_ects_default: int = 180):
    with kachel("BURN DOWN CHART: ZEITPLAN"):
        # Ziel-ECTS & bereits bestandene ECTS
        try:
            ects_bestanden = float(service.ects_summe_bestanden(student_id) or 0.0)
        except Exception:
            ects_bestanden = 0.0

        try:
            ziele = service.hole_studienziele(student_id)
        except Exception:
            ziele = None

        ziel_ects = (
            getattr(ziele, "ziel_ects", None)
            or getattr(ziele, "ects_ziel", None)
            or ziel_ects_default
        )

        # Zeitraum: von jetzt bis Ziel-Abschluss (oder +6 Monate)
        ziel_abschluss = getattr(ziele, "ziel_abschluss", None) or getattr(ziele, "ziel_abschlussdatum", None)
        start_d = date.today().replace(day=1)
        if isinstance(ziel_abschluss, date):
            end_d = ziel_abschluss
        else:
            # Default-Fenster
            end_d = (date.today().replace(day=1) + timedelta(days=31*6)).replace(day=1)

        # Monatsliste
        months = []
        cur = start_d
        while cur <= end_d:
            months.append(cur)
            if cur.month == 12:
                cur = cur.replace(year=cur.year + 1, month=1, day=1)
            else:
                cur = cur.replace(month=cur.month + 1, day=1)
        if not months:
            months = [start_d, start_d + timedelta(days=30)]

        # Ideal: linear von „Rest-ECTS“ auf 0
        total_span = max(len(months) - 1, 1)
        ideal_rest = [max(ziel_ects - (ects_bestanden * i / total_span), 0) for i, _ in enumerate(months)]

        # TODO Ist-Kurve: falls du monatliche Realwerte hast, hier einsetzen
        actual_rest = None

        x_labels = [m.strftime("%b %Y") for m in months]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_labels, y=ideal_rest, mode="lines+markers", name="Ideal"))
        if actual_rest is not None:
            fig.add_trace(go.Scatter(x=x_labels, y=actual_rest, mode="lines+markers", name="Ist"))
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Monat",
            yaxis_title="Rest-ECTS",
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
