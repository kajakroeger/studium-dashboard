"""
ui/pages/dashboard_page.py
Orchestriert die Dashboard-Seite: lädt den (einzigen) Studenten, Studiengang etc.
"""
from typing import Optional
import streamlit as st

from core import get_workflow_service

from core.viewmodel_builder import ViewModelBuilder
from core.workflow_service import WorkflowService
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


def render_dashboard_streamlit(vm_builder: ViewModelBuilder) -> None:
    """
    Rendert das Dashboard für genau einen Studenten.
    In dieser Version wird immer der erste vorhandene Student verwendet.
    """
    workflow = get_workflow_service()

    st.set_page_config(
        page_title="Studium Dashboard",
        page_icon="🎓",
        layout="wide",
    )
    st.title("🎓 Studium Dashboard")

    # 1) Studierende über den Service holen
    try:
        students = workflow.student_all()
    except Exception as e:
        st.error(f"Fehler beim Laden der Studenten: {e}")
        return 

    if not students:
        from ui.dialogs.onboarding import show_onboarding_dialog
        show_onboarding_dialog(workflow)
        st.info("Bitte lege zuerst einen Studenten an.")
        return


    # Hinweis: auch wenn mehrere in der DB sind, nutzen wir in dieser Version nur den ersten
    if len(students) > 1:
        st.warning(
            "Hinweis: In dieser Version des Dashboards wird nur der erste angelegte "
            "Student betrachtet."
        )

    # 2) In dieser Phase: immer den ersten Studenten verwenden
    student = students[0]
    student_id = student.id
    student_name = student.name

    # Optional: Infos zum aktuell verwendeten Studenten anzeigen
    st.caption(f"Aktueller Student: {student_name}")
    
    # 3) Studiengang auswählen/ermitteln
    studiengang_id = _select_studiengang(workflow, student_id)

    # Wichtig: Dashboard trotzdem anzeigen, auch wenn (noch) kein Studiengang vorhanden ist
    if not studiengang_id:
        st.info("Sobald ein Studiengang angelegt ist, werden hier alle Kacheln aktiviert.")
        return


    # 4) Action-Bar (Buttons) – braucht nur den Service + student_id
    render_action_bar(workflow, student_id)

    # 5) Debug – nur wenn IDs sicher gesetzt sind
    render_debug_info(workflow, student_id)

    # 1. Zeile: Studienziele und Status
    left, right = st.columns(2, gap="large")
    with left:
        studienziele_vm = vm_builder.build_studienziele(student_id, studiengang_id)
        render_studienziele(studienziele_vm)
    with right:
        studienziele_status_vm = vm_builder.build_studienziele_status(student_id, ziel_tage_pro_5ects=30.0)
        render_studienziele_status(studienziele_status_vm)

    # 2. Zeile: Status-Übersicht und Burndown Chart
    row2_left, row2_right = st.columns(2, gap="large")
    with row2_left:
        status_uebersicht_vm = vm_builder.build_status_uebersicht(student_id, studiengang_id)
        render_status_uebersicht(status_uebersicht_vm)
    with row2_right:
        burndown_chart_vm = vm_builder.build_burndown_chart(student_id, studiengang_id)
        render_burndown_chart(burndown_chart_vm)

    # 3. Zeile: Notenverlauf und Bearbeitungsverlauf
    row3_left, row3_right = st.columns(2, gap="large")
    with row3_left:
        notenverlauf_vm = vm_builder.build_notenverlauf(student_id, studiengang_id)
        render_notenverlauf(notenverlauf_vm)

    with row3_right:
        bearbeitungsverlauf_vm = vm_builder.build_bearbeitungsverlauf(student_id, studiengang_id)
        render_bearbeitungsverlauf(bearbeitungsverlauf_vm)

    # 4. Zeile: Kursplan
        kursplan_vm = vm_builder.build_kursplan(student_id, studiengang_id)
        render_kursplan_gantt(kursplan_vm)



def _select_studiengang(service: WorkflowService, student_id: int) -> Optional[int]:
    """
    Wählt den aktiven Studiengang oder – falls mehrere Einschreibungen bestehen –
    einen passenden Studiengang. Speichert die Auswahl zusätzlich in
    st.session_state["studiengang_id"].
    """
    workflow = get_workflow_service()

    try:
        einschreibungen = workflow.einschreibungen_fuer_student(student_id)
    except Exception as ex:
        st.error(f"Fehler beim Laden der Einschreibungen: {ex}")
        return None

    if not einschreibungen:
        return None

    aktive = [e for e in einschreibungen if e.ist_aktiv]
    auswahl = aktive if aktive else einschreibungen

    labels: list[str] = []
    ids: list[int] = []

    for e in auswahl:
        sg_id = e.studiengang_id
        sg = workflow.studiengang_by_id(sg_id)
        name = sg.name if sg is not None else f"Studiengang #{sg_id}"
        labels.append(name)
        ids.append(sg_id)

    if not ids:
        return None

    if len(ids) == 1:
        chosen = ids[0]
    else:
        idx = st.selectbox(
            "Studiengang",
            list(range(len(ids))),
            format_func=lambda i: labels[i],
        )
        chosen = ids[idx]

    st.session_state["studiengang_id"] = chosen
    return chosen
