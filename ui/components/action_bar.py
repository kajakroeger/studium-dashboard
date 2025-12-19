# ui/components/action_bar.py
from __future__ import annotations
from datetime import date
from typing import Optional
import streamlit as st
from core import WorkflowService, get_services
from models.pruefung import Pruefungsform


# =================== DIALOG-FUNKTIONEN ===================

workflow, progress = get_services()

@st.dialog("Kurs hinzufügen")
def add_kurs_dialog(workflow, progress, student_id: Optional[int], studiengang_id: Optional[int]):
    """Dialog zum Hinzufügen eines neuen Kurses."""
    st.caption("📘 Neuen Kurs anlegen")
    st.write(f"Student-ID: '{student_id}'")
    
    name = st.text_input("**Name***", key="dialog_add_name")
    kurs_kuerzel = st.text_input("**Kurskürzel***", key="dialog_add_kuerzel")
    ects = st.number_input("**ECTS***", min_value=1, max_value=30, step=1, value=5, key="dialog_add_ects")
    tutor = st.text_input("Tutor (optional)", key="dialog_add_tutor")

    # Live-Validierung für Name und Kürzel
    name_clean = name.strip()
    kuerzel_clean = kurs_kuerzel.strip()
    
    
    # Warnungen anzeigen, wenn Name/Kürzel bereits existieren
    if name_clean and workflow.kurs_name_exists(name_clean, studiengang_id):
        st.warning(f"⚠️ Ein Kurs mit dem Namen '{name_clean}' existiert bereits.")
    
    if kuerzel_clean and workflow.kurs_kuerzel_exists(kuerzel_clean, studiengang_id):
        st.warning(f"⚠️ Ein Kurs mit dem Kürzel '{kuerzel_clean}' existiert bereits.")

    pruefungsform = st.selectbox(
        "Prüfungsform (optional)",
        options=[None] + list(Pruefungsform),
        format_func=lambda v: "–" if v is None else v.value,
        key="dialog_add_pruefungsform",
    )

    c1, c2, c3 = st.columns(3)
    plan_start = c1.date_input("Geplanter Start (opt.)", value=None, key="dialog_add_plan_start")
    plan_end = c2.date_input("Geplante Abgabe (opt.)", value=None, key="dialog_add_plan_ende")
    start_datum = c3.date_input("Tatsächlicher Start (opt.)", value=None, key="dialog_add_start_datum")

    st.divider()
    col_cancel, col_save = st.columns([1, 1])
    
    if col_cancel.button("❌ Abbrechen", use_container_width=True):
        st.rerun()
    
    if col_save.button("💾 Speichern", type="primary", use_container_width=True):
        if not student_id:
            st.error("Bitte zuerst einen Studenten auswählen/anlegen.")
            return
        
        # Validierung
        if not name.strip():
            st.error("Bitte einen Namen eingeben.")
            return
        if not kurs_kuerzel.strip():
            st.error("Bitte ein Kurskürzel eingeben.")
            return
        
        try:
            workflow.kurs_hinzufuegen(
                student_id=student_id,
                studiengang_id=studiengang_id,
                name=name.strip(),
                kurs_kuerzel=kurs_kuerzel.strip(),
                ects=int(ects),
                tutor=(tutor.strip() or None),
                pruefungsform=pruefungsform,
                plan_start=plan_start or None,
                plan_end=plan_end or None,
                start_datum=start_datum or None,
            )
            progress.invalidate_cache(student_id=student_id, studiengang_id=studiengang_id)
            st.session_state["add_kurs__just_saved"] = True
            st.rerun()
        except Exception as ex:
            st.error(f"❌ Speichern fehlgeschlagen: {ex}")




@st.dialog("Kurs starten")
def start_kurs_dialog(workflow, progress, student_id: Optional[int], studiengang_id: Optional[int]):
    """
    Dialog zum Starten eines Kurses.
    Es werden nur Bearbeitungen ohne start_datum und nicht 'abgeschlossen' angezeigt.
    """
    st.caption("▶ Kursbearbeitung starten")

    if not student_id:
        st.error("Bitte zuerst einen Studenten auswählen/anlegen.")
        return

    # Kandidaten zum Starten filtern
    startbare_items = workflow.inaktive_bearbeitungen(student_id, studiengang_id)

    if not startbare_items:
        st.info("Es gibt derzeit keine Kurse, die gestartet werden können.")
        st.caption("💡 Füge einen Kurs hinzu oder trage erst die Planung ein.")
        return

    # Selectbox vorbereiten
    labels = [lbl for _, _, lbl in startbare_items]
    idx = st.selectbox(
        "**Kurs auswählen***",
        list(range(len(labels))),
        format_func=lambda i: labels[i],
        key="start_kurs_idx",
    )
    bearbeitung, kurs, _ = startbare_items[idx]

    start_datum = st.date_input(
        "**Startdatum***",
        value=date.today(),
        key="start_kurs_startdatum",
    )

    st.divider()
    c1, c2 = st.columns(2)

    if c1.button("❌ Abbrechen", use_container_width=True):
        st.rerun()

    if c2.button("▶ Kurs starten", type="primary", use_container_width=True):
        try:
            # hier rufen wir eine Service-Methode auf (siehe unten)
            workflow.bearbeitung_starten(
                bearbeitung_id=getattr(bearbeitung, "id", None),
                start_datum=start_datum,
            )
            progress.invalidate_cache(student_id=student_id, studiengang_id=studiengang_id)
            st.session_state["start_kurs__just_saved"] = True
            st.rerun()
        except Exception as ex:
            st.error(f"❌ Fehler beim Starten des Kurses: {ex}")



@st.dialog("Prüfung abgeben")
def submit_pruefung_dialog(workflow, progress, student_id: Optional[int], studiengang_id: Optional[int]):
    st.caption("📝 Kurs wählen und Abgabedatum setzen")

    if not student_id:
        st.error("Bitte zuerst einen Studenten auswählen/anlegen.")
        return

    try:
        items = workflow.aktive_bearbeitungen(student_id, studiengang_id)  # (b, kurs, label)
    except Exception as ex:
        st.error(f"Fehler beim Laden der Kurse: {ex}")
        return

    if not items:
        st.info("Keine aktiven Kurse vorhanden, die eingereicht werden können.")
        st.caption("💡 Tipp: Füge zuerst einen Kurs hinzu und starte die Bearbeitung.")
        return

    labels = [lbl for _, _, lbl in items]
    idx = st.selectbox(
        "**Kurs***",
        options=list(range(len(labels))),
        format_func=lambda i: labels[i],
        key="submit_kurs_idx",
    )

    _, kurs, _ = items[idx]
    kurs_id = int(kurs.id)

    abgabe = st.date_input("**Abgabedatum***", value=date.today(), key="submit_abgabe")

    st.divider()
    col_cancel, col_save = st.columns([1, 1])

    if col_cancel.button("❌ Abbrechen", use_container_width=True):
        st.rerun()

    if col_save.button("📤 Abgeben", type="primary", use_container_width=True):
        try:
            workflow.pruefung_abgeben(
                student_id=student_id,
                kurs_id=kurs_id,
                abgabe_datum=abgabe,
            )
            progress.invalidate_cache(student_id=student_id, studiengang_id=studiengang_id)
            st.session_state["submit_pruefung__just_saved"] = True
            st.rerun()
        except Exception as ex:
            st.error(f"❌ Fehler beim Abgeben: {ex}")



@st.dialog("Bewertung eintragen")
def add_bewertung_dialog(workflow, progress, student_id: Optional[int], studiengang_id: Optional[int]):
    st.caption("⭐ Note für eingereichte Prüfungen eintragen")

    if not student_id:
        st.error("Bitte zuerst einen Studenten auswählen/anlegen.")
        return

    try:
        items = workflow.eingereichte_bearbeitungen(student_id, studiengang_id)  # (b, kurs, pruef, label)
    except Exception as ex:
        st.error(f"Fehler beim Laden der offenen Bewertungen: {ex}")
        return

    if not items:
        st.info(
            "Aktuell gibt es keine Bearbeitungen mit Status 'Prüfung eingereicht', "
            "die bewertet werden können."
        )
        return

    labels = [lbl for _, _, _, lbl in items]
    idx = st.selectbox(
        "**Kurs / Bearbeitung***",
        options=list(range(len(labels))),
        format_func=lambda i: labels[i],
        key="dialog_grade_bearbeitung_idx",
    )

    bearb, kurs, _, _ = items[idx]

    note = st.number_input(
        "**Note*** (1.0 - 5.0)",
        min_value=1.0,
        max_value=5.0,
        step=0.1,
        value=1.0,
        format="%.1f",
        key="dialog_grade_note",
    )

    st.info("💡 1.0 = sehr gut, 5.0 = nicht bestanden")

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("❌ Abbrechen", use_container_width=True):
        st.rerun()

    if c2.button("💾 Speichern", type="primary", use_container_width=True):
        try:
            p = workflow.note_eintragen(
                student_id=student_id,
                kurs_id=int(kurs.id),
                note=float(note),
            )
            progress.invalidate_cache(student_id=student_id, studiengang_id=studiengang_id)

            st.session_state["add_bewertung__just_saved"] = True
            st.session_state["last_pruefung_info"] = {
                "versuch_nr": getattr(p, "versuch_nr", None),
                "bestanden": getattr(p, "bestanden", None),
            }
            st.rerun()
        except Exception as ex:
            st.error(f"❌ Fehler beim Speichern: {ex}")



@st.dialog("Studium abschließen")
def finish_studium_dialog(workflow, progress, student_id: Optional[int], studiengang_id: Optional[int]):
    st.caption("🎓 Abschluss prüfen und Studium beenden")
    st.warning("⚠️ Voraussetzungen: ECTS erreicht + Abschlussprüfung bestanden")

    if not student_id or not studiengang_id:
        st.error("Bitte zuerst einen Studenten und einen Studiengang auswählen.")
        return

    # --- ECTS laden ---
    daten = progress.status_uebersicht_daten(student_id, studiengang_id)

    if not daten or daten.ects_gesamt is None:
        st.error("❌ Studiengang nicht korrekt geladen.")
        return

    ects_bestanden = int(daten.ects_bestanden or 0.0)
    ziel_ects = int(daten.ects_gesamt)
    genug_ects = ects_bestanden >= ziel_ects
    notenschnitt = daten.notenschnitt

    st.info(f"📚 **ECTS-Fortschritt:** {ects_bestanden:.0f} / {ziel_ects} ECTS")
    if not genug_ects:
        st.error("❌ Ziel-ECTS noch nicht erreicht.")

    st.divider()
    col_cancel, col_save = st.columns([1, 1])

    if col_cancel.button("❌ Abbrechen", use_container_width=True):
        st.rerun()

    if col_save.button(
        "✅ Abschließen",
        type="primary",
        use_container_width=True,
        disabled=not genug_ects,
    ):
        try:
            ok = workflow.studium_abschliessen(
                student_id=student_id,
                studiengang_id=studiengang_id,
                notenschnitt=notenschnitt,
            )
            if ok:
                progress.invalidate_cache(student_id=student_id, studiengang_id=studiengang_id)
                st.session_state["finish_studium__success"] = True
                st.rerun()
            else:
                st.warning("❌ Bedingungen noch nicht erfüllt (ECTS/Abschlussprüfung).")
        except Exception as ex:
            st.error(f"❌ Fehler: {ex}")



@st.dialog("Einstellungen")
def settings_dialog(student_id: Optional[int], studiengang_id: Optional[int]):
    """Dialog für Einstellungen."""
    st.caption("⚙️ Anwendungseinstellungen")
    
    st.info("Hier kannst du demnächst Einstellungen vornehmen, wie")
    st.markdown("""
    - 🌙 Dark Mode umschalten
    - 👤 Namen ändern
    - 🎯 Ziel-Notendurchschnitt festlegen
    - 📊 Anzeigeeinstellungen
    """)
    
    st.divider()
    
    # Platzhalter für zukünftige Features
    theme = st.selectbox("Theme (Platzhalter)", ["Auto", "Hell", "Dunkel"], disabled=True)
    ziel_durchschnitt = st.number_input("Ziel-Notendurchschnitt", value=2.0, min_value=1.0, max_value=4.0, step=0.1, disabled=True)
    
    st.divider()
    
    if st.button("Schließen", use_container_width=True):
        st.rerun()


# =================== HAUPT-ACTION-BAR ===================

def render_action_bar(
    workflow: WorkflowService,
    student_id: Optional[int],
    studiengang_id: Optional[int],
) -> None:
    """Eine Zeile von Buttons – jeder Button öffnet einen eigenen Dialog."""
    
    # Toast-Nachrichten für erfolgreiche Aktionen
    if st.session_state.get("add_kurs__just_saved", False):
        st.session_state["add_kurs__just_saved"] = False
        st.toast("✅ Kurs erfolgreich gespeichert!")

    if st.session_state.get("start_kurs__just_saved", False):
        st.session_state["start_kurs__just_saved"] = False
        st.toast("▶ Kursbearbeitung gestartet!")
    
    if st.session_state.get("submit_pruefung__just_saved", False):
        st.session_state["submit_pruefung__just_saved"] = False
        st.toast("✅ Prüfung erfolgreich abgegeben!")

    if st.session_state.get("add_bewertung__just_saved", False):
        st.session_state["add_bewertung__just_saved"] = False
        info = st.session_state.get("last_pruefung_info", {})
        versuch = info.get("versuch_nr", "?")
        bestanden = info.get("bestanden", False)
        status = "✅ bestanden" if bestanden else "❌ nicht bestanden"
        st.toast(f"✅ Bewertung gespeichert! Versuch #{versuch}, {status}")
    
    if st.session_state.get("finish_studium__success", False):
        st.session_state["finish_studium__success"] = False
        st.toast("🎉 Glückwunsch! Studium erfolgreich abgeschlossen!")
    
    # Button-Leiste
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        if st.button("➕ Kurs hinzufügen", use_container_width=True, key="open_add_kurs"):
            st.session_state["show_add_kurs_dialog"] = True

    with col2:
        if st.button("▶️ Kurs starten", use_container_width=True, key="open_start_kurs"):
            st.session_state["show_start_kurs_dialog"] = True
    
    with col3:
        if st.button("📝 Prüfung abgeben", use_container_width=True, key="open_submit_pruefung"):
            st.session_state["show_submit_pruefung_dialog"] = True
    
    with col4:
        if st.button("⭐ Note eintragen", use_container_width=True, key="open_add_bewertung"):
            st.session_state["show_add_bewertung_dialog"] = True
    
    with col5:
        if st.button("🎓 Studium abschließen", use_container_width=True, key="open_finish_studium"):
            st.session_state["show_finish_studium_dialog"] = True
    
    with col6:
        if st.button("⚙️ Einstellungen", use_container_width=True, key="open_settings"):
            st.session_state["show_settings_dialog"] = True


    # Dialoge aufrufen
    if st.session_state.get("show_add_kurs_dialog", False):
        st.session_state["show_add_kurs_dialog"] = False
        add_kurs_dialog(workflow, progress, student_id, studiengang_id)

    if st.session_state.get("show_start_kurs_dialog", False):
        st.session_state["show_start_kurs_dialog"] = False
        start_kurs_dialog(workflow, progress, student_id, studiengang_id)
    
    if st.session_state.get("show_submit_pruefung_dialog", False):
        st.session_state["show_submit_pruefung_dialog"] = False
        submit_pruefung_dialog(workflow, progress, student_id, studiengang_id)
    
    if st.session_state.get("show_add_bewertung_dialog", False):
        st.session_state["show_add_bewertung_dialog"] = False
        add_bewertung_dialog(workflow, progress, student_id, studiengang_id)
    
    if st.session_state.get("show_finish_studium_dialog", False):
        st.session_state["show_finish_studium_dialog"] = False
        finish_studium_dialog(workflow, progress, student_id, studiengang_id)
    
    if st.session_state.get("show_settings_dialog", False):
        st.session_state["show_settings_dialog"] = False
        settings_dialog(student_id, progress, studiengang_id)