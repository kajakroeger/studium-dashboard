"""
ui/pages/dashboard_page.py
Orchestriert die Dashboard-Seite: Auswahl, Laden, Komponenten rendern.
"""
from typing import Optional
import streamlit as st
from db.repositories.student_repository import StudentRepository
from ui.components.action_bar import render_action_bar

# Kachel-Komponenten
from ui.components.studienziele import render_studienziele
from ui.components.studienziele_status import render_studienziele_status
from ui.components.status_uebersicht import render_status_uebersicht
from ui.components.burndown_chart import render_burndown_chart

def render_dashboard(service, students: StudentRepository):
    st.title("🎓 Studium Dashboard")

    alle = list(students.all())
    if not alle:
        from ui.dialogs.onboarding import show_onboarding_dialog
        show_onboarding_dialog(service)
        st.info("Bitte lege zuerst einen Studenten an.")
        return

    # Sidebar: Auswahl
    student_id = _student_selectbox(students)
    if student_id is None:
        st.info("Bitte wähle einen Studenten in der Sidebar aus.")
        return

    # Action-Bar
    render_action_bar(service, students, student_id)

    # ===== Row 1: Studienziele + Aktueller Status =====
    left, right = st.columns(2, gap="large")
    with left:
        render_studienziele(service, student_id)
    with right:
        render_studienziele_status(service, student_id)

    # ===== Row 2: Status Übersicht + Burn-Down =====
    row2_left, row2_right = st.columns(2, gap="large")
    with row2_left:
        render_status_uebersicht(service, student_id)
    with row2_right:
        render_burndown_chart(service, student_id)

def _student_selectbox(students: StudentRepository) -> Optional[int]:
    alle = list(students.all())
    if not alle:
        return None
    labels = [f"{s.id} – {getattr(s, 'name', str(s))}" for s in alle]
    index = st.sidebar.selectbox("Student", options=list(range(len(alle))), format_func=lambda i: labels[i])
    return alle[index].id
