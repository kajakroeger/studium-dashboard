# ui/dialogs/onboarding.py
"""
Zweistufiges Onboarding:
1) Student + Ziele
2) Studiengang (Name, Monate, Kurse, ECTS)
"""
from __future__ import annotations
import streamlit as st
from datetime import date
from core import WorkflowService, ProgressService

def _init_state() -> None:
    st.session_state.setdefault("onb_step", 1)
    st.session_state.setdefault("onb_form", {})  

def _step1() -> None:
    st.subheader("Schritt 1/2 – Deine Daten & Studienziele")
    with st.form("onb_step1"):
        name = st.text_input("Username *")
        matrikel = st.text_input("Matrikelnummer *")
        email = st.text_input("E-Mail (optional)")
        uni_email = st.text_input("Uni-E-Mail (optional)")
        col1, col2 = st.columns(2)
        ziel_noten = col1.number_input("Ziel-Notenschnitt *", 1.0, 5.0, step=0.1, format="%.1f", value=2.0)
        ziel_end = col2.date_input("Zieldatum Bachelorarbeit *", value=date.today())
        next_btn = st.form_submit_button("Weiter ➜", type="primary")
        if next_btn:
            if not name or not matrikel:
                st.error("Name und Matrikelnummer sind Pflicht.")
                return
            st.session_state.onb_form.update(
                dict(name=name, matrikel=matrikel, email=email or None, uni_email=uni_email or None,
                     ziel_noten=float(ziel_noten), ziel_end=ziel_end)
            )
            st.session_state.onb_step = 2
            st.rerun()

def _step2(workflow: WorkflowService, progress: ProgressService) -> None:
    st.subheader("Schritt 2/2 – Dein Studiengang")
    with st.form("onb_step2"):
        sg_name = st.text_input("Studiengang-Name *", placeholder="z. B. B.Sc. Softwareentwicklung")
        sem_anzahl = st.number_input("Anzahl der Semester *", min_value=1, max_value=120, step=1, value=6)
        col1, col2 = st.columns(2)
        monate = col1.number_input("Anzahl Monate *", min_value=1, max_value=120, step=1, value=36)
        kurse = col2.number_input("Anzahl Kurse *", min_value=1, max_value=60, step=1, value=30)
        ects = st.number_input("ECTS gesamt *", min_value=30, max_value=480, step=5, value=180)
        back = st.form_submit_button("← Zurück")
        save = st.form_submit_button("Speichern", type="primary")
        if back:
            st.session_state.onb_step = 1
            st.rerun()
        if save:
            f = st.session_state.onb_form
            try:
                student_id, studiengang_id_new = workflow.onboarding(
                    student_name=f["name"],
                    matrikelnummer=f["matrikel"],
                    email=f["email"],
                    uni_email=f["uni_email"],
                    studiengang_name=sg_name,
                    anzahl_monate=int(monate),
                    anzahl_kurse=int(kurse),
                    ects_gesamt=int(ects),
                    semester_anzahl=int(sem_anzahl),
                    ziel_notenschnitt=float(f["ziel_noten"]),
                    ziel_enddatum=f["ziel_end"],
                )

                # wichtig: ausgewählten Studiengang setzen, damit Dashboard sofort passt
                st.session_state["studiengang_id"] = studiengang_id_new

                # Cache invalidieren, damit neue Daten sichtbar werden
                progress.invalidate_cache(student_id=student_id, studiengang_id=studiengang_id_new)

                st.success("Gespeichert! Dashboard wird aktualisiert …")
                st.session_state.pop("onb_form", None)
                st.session_state.pop("onb_step", None)
                st.rerun()

            except Exception as ex:
                st.error(f"Fehler beim Anlegen: {ex}")

def show_onboarding_dialog(workflow: WorkflowService, progress: ProgressService) -> None:
    _init_state()
    if hasattr(st, "modal"):
        with st.modal("Willkommen 👋 – Lass uns starten!"):
            if st.session_state.onb_step == 1:
                _step1()
            else:
                _step2(workflow, progress)
    elif hasattr(st, "dialog"):
        @st.dialog("Willkommen 👋 – Lass uns starten!")
        def _dlg():
            if st.session_state.onb_step == 1:
                _step1()
            else:
                _step2(workflow, progress)
        _dlg()
    else:
        with st.expander("👋 Willkommen – Lass uns starten!", expanded=True):
            if st.session_state.onb_step == 1:
                _step1()
            else:
                _step2(workflow, progress)
