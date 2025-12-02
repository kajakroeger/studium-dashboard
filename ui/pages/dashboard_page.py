"""
ui/pages/dashboard_page.py
Orchestriert die Dashboard-Seite: lädt den (einzigen) Studenten, Studiengang etc.
"""
from typing import Optional
import streamlit as st

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


def render_dashboard(service) -> None:
    """
    Rendert das Dashboard für genau einen Studenten.
    In dieser Version wird immer der erste vorhandene Student verwendet.
    """
    st.title("🎓 Studium Dashboard")

    # 1) Studierende über den Service holen
    try:
        students = service.student_all()
    except Exception as e:
        st.error(f"Fehler beim Laden der Studenten: {e}")
        raise 

    if not students:
        from ui.dialogs.onboarding import show_onboarding_dialog
        show_onboarding_dialog(service)
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

    # Optional: Infos zum aktuell verwendeten Studenten anzeigen
    st.caption(f"Aktueller Student: {getattr(student, 'name', f'ID {student_id}')}")
    
    # 3) Studiengang auswählen/ermitteln
    studiengang_id = _select_studiengang(service, student_id)

    # Wichtig: Dashboard trotzdem anzeigen, auch wenn (noch) kein Studiengang vorhanden ist
    if not studiengang_id:
        st.warning(
            "⚠️ Kein aktiver Studiengang gefunden. "
            "Bitte lege zuerst einen Studiengang an."
        )

    # 4) Action-Bar (Buttons) – braucht nur den Service + student_id
    render_action_bar(service, student_id)

    # 5) Debug – nur wenn IDs sicher gesetzt sind
    render_debug_info(service, student_id)

    # 1. Zeile: Studienziele und Status
    if studiengang_id:
        left, right = st.columns(2, gap="large")
        with left:
            render_studienziele(service, student_id)
        with right:
            render_studienziele_status(service, student_id)
    else:
        st.info("Studienziele werden angezeigt, sobald ein Studiengang angelegt ist.")

    # 2. Zeile: Status-Übersicht und Burndown Chart
    row2_left, row2_right = st.columns(2, gap="large")
    with row2_left:
        if studiengang_id:
            render_status_uebersicht(service, student_id, studiengang_id)
        else:
            st.info(
                "Status-Übersicht wird angezeigt, sobald ein Studiengang angelegt ist."
            )
    with row2_right:
        if studiengang_id:
            render_burndown_chart(service, student_id, studiengang_id)
        else:
            st.info(
                "Burndown Chart wird angezeigt, sobald ein Studiengang angelegt ist."
            )

    # 3. Zeile: Notenverlauf und Bearbeitungsverlauf
    row3_left, row3_right = st.columns(2, gap="large")
    with row3_left:
        if studiengang_id:
            render_notenverlauf(service, student_id, studiengang_id)
        else:
            st.info(
                "Notenverlauf wird angezeigt, sobald ein Studiengang angelegt ist."
            )
    with row3_right:
        if studiengang_id:
            render_bearbeitungsverlauf(service, student_id, studiengang_id)
        else:
            st.info(
                "Bearbeitungsverlauf wird angezeigt, sobald ein Studiengang angelegt ist."
            )

    # 4. Zeile: Kursplan
    if studiengang_id:
        render_kursplan_gantt(service, student_id, studiengang_id)
    else:
        st.info(
            "Kursplan wird angezeigt, sobald ein Studiengang angelegt ist."
        )


def _select_studiengang(service, student_id: int) -> Optional[int]:
    """
    Wählt den aktiven Studiengang oder – falls mehrere Einschreibungen bestehen –
    einen passenden Studiengang. Speichert die Auswahl zusätzlich in
    st.session_state["studiengang_id"].
    """
    get_all = getattr(service, "einschreibungen_fuer_student", None)
    if not callable(get_all):
        return None
        
    einschreibungen = get_all(student_id)
    if not einschreibungen:
        return None

    # Nur aktive Einschreibungen filtern (falls Status gesetzt)
    aktive = [e for e in einschreibungen if e.ist_aktiv]
    auswahl = aktive if aktive else einschreibungen

    labels: list[str] = []
    ids: list[int] = []

    for e in auswahl:
        sg_id = e.studiengang_id
        sg = service.studiengang_by_id(sg_id)
        if sg is not None:
            name = sg.name
        else:
            name = f"Studiengang #{sg_id}"
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
            format_func=lambda i: labels[i]
        )
        chosen = ids[idx]

    st.session_state["studiengang_id"] = chosen
    return chosen
    
    
    # TODO: Hier kann ein Dropdown angeboten werden, um den Studiengang zu wählen 
    # else:
    #     idx = st.selectbox(
    #         "Studiengang",
    #         list(range(len(ids))),
    #         format_func=lambda i: labels[i]
    #     )
    #     chosen = ids[idx]

    # st.session_state["studiengang_id"] = chosen
    # return chosen
