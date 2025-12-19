# ui/pages/dashboard_page_streamlit.py
from typing import Optional
import streamlit as st

from core import get_progress_service, get_workflow_service

from core.viewmodel_builder import ViewModelBuilder
from core.workflow_service import WorkflowService
from ui.components.action_bar import render_action_bar

# Kachel-Komponenten
from ui.components.kursplan import render_kursplan_gantt
from ui.components.studienziele import render_studienziele
from ui.components.studienziele_status import render_studienziele_status
from ui.components.status_uebersicht import render_status_uebersicht
from ui.components.burndown_chart import render_burndown_chart
from ui.components.notenverlauf import render_notenverlauf
from ui.components.bearbeitungsverlauf import render_bearbeitungsverlauf

from ui.components.debug_info import render_debug_info

def render_dashboard_streamlit(vm_builder: ViewModelBuilder) -> None:
    """
    🧑‍💼🍽️ RESTAURANT-MANAGER (SEITEN-ORCHESTRATOR)
    - empfängt den USER / GAST
    - koordiniert den Ablauf der Seite und sorgt dafür,
    dass die richtigen Gerichte im richtigen Servierstil (Streamlit) erscheinen

    Technisch:
    - Streamlit-spezifische Seite (Layout, session_state, Dialoge)
    - KEINE Geschäftslogik, KEINE Berechnungen
    - KEINE direkten Datenbankzugriffe

    Verantwortlich für Seiten-Orchestrierung:
    - Page Config (Titel, Layout, Icon)
    - Auswahl & Verwaltung des Kontexts entsprechend nach Student und Studiengang
    - Steuerung des Seitenflusses:
        - Onboarding, falls noch keine Daten existieren
        - Anzeigen von Hinweisen / Warnungen
    - Layout & Reihenfolge der Kacheln:
        - Spalten / Zeilen
        - Gruppierung der UI-Komponenten
        
    Zusammenarbeit:
    - nutzt WorkflowService **nur** für Kontext- & Auswahl-Daten (z. B. Studenten, Studiengang-Optionen)
    - nutzt ViewModelBuilder zur Erstellung der ViewModels
    - UI-Komponenten rendern ausschließlich die ViewModels        
    """
    workflow = get_workflow_service()
    progress = get_progress_service()

    st.set_page_config(
        page_title="Studium Dashboard",
        page_icon="🎓",
        layout="wide",
    )

    # 1) Studierende über den Service holen
    try:
        students = workflow.student_all()
    except Exception as e:
        st.error(f"Fehler beim Laden der Studenten: {e}")
        return

    if not students:
        from ui.dialogs.onboarding import show_onboarding_dialog
        show_onboarding_dialog(workflow, progress)
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
    student_name = getattr(student, "name", "–")

    # 3) Studiengang auswählen/ermitteln (WICHTIG: bevor wir ihn irgendwo benutzen)
    studiengang_id = _select_studiengang(workflow, student_id)

    # Titel + Kontext anzeigen (jetzt haben wir die Daten)
    sg = workflow.studiengang_by_id(studiengang_id) if studiengang_id else None
    sg_name = sg.name if sg else None

    title = "🎓 Studium Dashboard"
    if sg_name:
        title = f"🎓 Studium Dashboard – {sg_name}"
    st.title(title)

    st.caption(f"Aktueller Student: {student_name}")

    # Wichtig: Dashboard trotzdem anzeigen, auch wenn (noch) kein Studiengang vorhanden ist
    if not studiengang_id:
        st.info("Sobald ein Studiengang angelegt ist, werden hier alle Kacheln aktiviert.")
        return

    # 4) Action-Bar (Buttons)
    render_action_bar(workflow, student_id, studiengang_id)

    # 5) Debug
    render_debug_info(workflow, student_id, studiengang_id)

    # 1. Zeile: Studienziele und Status
    left, right = st.columns(2, gap="large")
    with left:
        studienziele_vm = vm_builder.build_studienziele(student_id, studiengang_id)
        render_studienziele(studienziele_vm)
    with right:
        # Hinweis: wenn du studiengang-spezifische Ziele willst, solltest du studiengang_id auch hier durchreichen
        studienziele_status_vm = vm_builder.build_studienziele_status(
            student_id,
            studiengang_id,
            ziel_tage_pro_5ects=30.0,
        )
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


def _select_studiengang(workflow: WorkflowService, student_id: int) -> Optional[int]:
    opts = workflow.studiengang_options_fuer_student(student_id)
    if not opts:
        return None

    ids = [o.id for o in opts]
    saved = st.session_state.get("studiengang_id")

    # default index bestimmen
    if saved in ids:
        default_index = ids.index(saved)
    else:
        default_index = next((i for i, o in enumerate(opts) if o.ist_default), 0)

    chosen_opt = st.selectbox(
        "Studiengang",
        options=opts,
        index=default_index,
        format_func=lambda o: o.label,
        key="studiengang_select",
    )

    chosen_id = chosen_opt.id
    st.session_state["studiengang_id"] = chosen_id
    return chosen_id


