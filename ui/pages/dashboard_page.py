"""
ui/pages/dashboard_page.py
Orchestriert die Dashboard-Seite: Auswahl, Laden, Komponenten rendern.
"""
from typing import Optional
import streamlit as st
from db.repositories.student_repository import StudentRepository
from ui.components.goals import render_goals_row

from ui.components.action_bar import render_action_bar

def render_dashboard(service, students):
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

    # Action-Bar oben
    render_action_bar(service, students, student_id)

    # Ziele + Status
    render_goals_row(service, student_id)




def _student_selectbox(students: StudentRepository) -> Optional[int]:
    alle = list(students.all())
    if not alle:
        return None
    labels = [f"{s.id} – {getattr(s, 'name', str(s))}" for s in alle]
    index = st.sidebar.selectbox("Student", options=list(range(len(alle))), format_func=lambda i: labels[i])
    return alle[index].id
