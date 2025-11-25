"""
ui/pages/dashboard_page.py
Orchestriert die Dashboard-Seite: Auswahl, Laden, Komponenten rendern.
"""
from typing import Optional
import streamlit as st
from db.repositories.student_repository import StudentRepository
from ui.components.action_bar import render_action_bar
from ui.components.debug_info import render_debug_info

# Kachel-Komponenten
from ui.components.kursplan import render_kursplan_gantt
from ui.components.studienziele import render_studienziele
from ui.components.studienziele_status import render_studienziele_status
from ui.components.status_uebersicht import render_status_uebersicht
from ui.components.burndown_chart import render_burndown_chart
from ui.components.notenverlauf import render_notenverlauf
from ui.components.bearbeitungsverlauf import render_bearbeitungsverlauf


def render_dashboard(service, students: StudentRepository):
    st.title("🎓 Studium Dashboard")

    # 1) Gibt es überhaupt Studierende?
    alle = list(students.all())
    if not alle:
        # Onboarding anbieten und danach **sofort** raus
        from ui.dialogs.onboarding import show_onboarding_dialog
        show_onboarding_dialog(service)
        st.info("Bitte lege zuerst einen Studenten an.")
        return  # <-- WICHTIG: hier wirklich beenden!

    # 2) Student auswählen (Sidebar)
    student_id = _student_selectbox(students)
    if student_id is None:
        st.info("Bitte wähle einen Studenten in der Sidebar aus.")
        return

    # 3) Studiengang auswählen (Dropdown falls mehrere)
    studiengang_id = _select_studiengang(service, student_id)
    
    # WICHTIG: Nur warnen, aber nicht abbrechen - zeige trotzdem das Dashboard
    if not studiengang_id:
        st.warning("⚠️ Kein aktiver Studiengang gefunden. Bitte lege zuerst einen Studiengang an.")
        # Nicht return! Dashboard soll trotzdem angezeigt werden

    # 4) Action-Bar (Buttons)
    render_action_bar(service, students, student_id)

    # 5) Debug – nur wenn IDs sicher gesetzt sind
    render_debug_info(service, students, student_id, studiengang_id)

    # 1. Erste Zeile: Studienziele und Status
    if studiengang_id:
        left, right = st.columns(2, gap="large")
        with left:
            render_studienziele(service, student_id)
        with right:
            render_studienziele_status(service, student_id)

    # 2. Zeile: Status-Übersicht und Burndown Chart
    row2_left, row2_right = st.columns(2, gap="large")
    with row2_left:
        if studiengang_id:
            render_status_uebersicht(service, student_id, studiengang_id)
        else:
            st.info("Status-Übersicht wird angezeigt, sobald ein Studiengang angelegt ist.")
    with row2_right:
        # Burndown Chart funktioniert auch ohne studiengang_id (nutzt nur student_id)
        try:
            render_burndown_chart(service, student_id)
        except TypeError:
            # Falls die alte Signatur mit studiengang_id noch erwartet wird
            if studiengang_id:
                render_burndown_chart(service, student_id, studiengang_id)
            else:
                st.info("Burndown Chart wird angezeigt, sobald ein Studiengang angelegt ist.")

    # 3. Zeile: Notenverlauf und Bearbeitungsverlauf
    row3_left, row3_right = st.columns(2, gap="large")
    with row3_left:
        render_notenverlauf(service, student_id)
    with row3_right:
        render_bearbeitungsverlauf(service, student_id)

    # 4. Zeile
    render_kursplan_gantt(service, student_id)   



def _student_selectbox(students: StudentRepository) -> Optional[int]:
    """Sidebar-Selectbox für Student-Auswahl."""
    alle = list(students.all())
    if not alle:
        return None
    labels = [f"{s.id} – {getattr(s, 'name', str(s))}" for s in alle]
    index = st.sidebar.selectbox(
        "Student",
        options=list(range(len(alle))),
        format_func=lambda i: labels[i]
    )
    return alle[index].id


def _select_studiengang(service, student_id: int) -> Optional[int]:
    """
    Wählt den aktiven Studiengang oder – bei mehreren – per Dropdown.
    Speichert die Auswahl zusätzlich in st.session_state["studiengang_id"].
    """
    get_all = getattr(service, "einschreibungen_fuer_student", None)
    if not callable(get_all):
        return None
        
    einschreibungen = get_all(student_id)
    if not einschreibungen:
        return None

    aktive = [
        e for e in einschreibungen
        if str(getattr(e, "status", "")).strip().lower() in {"aktiv", "laufend"}
    ]
    auswahl = aktive if aktive else einschreibungen

    labels, ids = [], []
    for e in auswahl:
        sg_id = getattr(e, "studiengang_id", None)
        get_sg = getattr(service, "studiengang_by_id", None)
        sg = get_sg(sg_id) if callable(get_sg) and sg_id else None
        name = getattr(sg, "name", f"Studiengang #{sg_id}") if sg else f"Studiengang #{sg_id}"
        labels.append(name)
        ids.append(sg_id)

    if not ids:
        return None
        
    if len(ids) == 1:
        chosen = ids[0]
    else:
        idx = st.selectbox("Studiengang", list(range(len(ids))), format_func=lambda i: labels[i])
        chosen = ids[idx]

    st.session_state["studiengang_id"] = chosen
    return chosen