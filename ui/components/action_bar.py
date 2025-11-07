# ui/components/action_bar.py

from __future__ import annotations
from datetime import date
import sqlite3
from typing import Optional
import streamlit as st
from core import FortschrittService
from db.repositories.student_repository import StudentRepository
from models.pruefung import Pruefungsform


# =================== DIALOG-FUNKTIONEN ===================

@st.dialog("Kurs hinzufügen")
def add_kurs_dialog(service: FortschrittService, current_student_id: Optional[int]):
    """Dialog zum Hinzufügen eines neuen Kurses."""
    st.caption("📘 Neuen Kurs anlegen")
    
    name = st.text_input("**Name***", key="dialog_add_name")
    kuerzel = st.text_input("**Kurskürzel***", key="dialog_add_kuerzel")
    ects = st.number_input("**ECTS***", min_value=1, max_value=30, step=1, value=5, key="dialog_add_ects")
    tutor = st.text_input("Tutor (optional)", key="dialog_add_tutor")

    # Live-Validierung für Name und Kürzel
    name_clean = name.strip()
    kuerzel_clean = kuerzel.strip()
    
    # Warnungen anzeigen, wenn Name/Kürzel bereits existieren
    if name_clean and service.kurs_name_exists(name_clean):
        st.warning(f"⚠️ Ein Kurs mit dem Namen '{name_clean}' existiert bereits.")
    
    if kuerzel_clean and service.kurs_kuerzel_exists(kuerzel_clean):
        st.warning(f"⚠️ Ein Kurs mit dem Kürzel '{kuerzel_clean}' existiert bereits.")

    pruefungsform = st.selectbox(
        "Prüfungsform (optional)",
        options=[None] + list(Pruefungsform),
        format_func=lambda v: "–" if v is None else v.value,
        key="dialog_add_pruefungsform",
    )

    c1, c2, c3 = st.columns(3)
    plan_start = c1.date_input("Geplanter Start (opt.)", value=None, key="dialog_add_plan_start")
    plan_ende = c2.date_input("Geplante Abgabe (opt.)", value=None, key="dialog_add_plan_ende")
    start_datum = c3.date_input("Tatsächlicher Start (opt.)", value=None, key="dialog_add_start_datum")

    st.divider()
    col_cancel, col_save = st.columns([1, 1])
    
    if col_cancel.button("❌ Abbrechen", use_container_width=True):
        st.rerun()
    
    if col_save.button("💾 Speichern", type="primary", use_container_width=True):
        if not current_student_id:
            st.error("Bitte zuerst einen Studenten auswählen/anlegen.")
            return
        
        # Validierung
        if not name.strip():
            st.error("Bitte einen Namen eingeben.")
            return
        if not kuerzel.strip():
            st.error("Bitte ein Kurskürzel eingeben.")
            return
        
        try:
            service.add_kurs_mit_bearbeitung_und_pruefung(
                student_id=current_student_id,
                name=name.strip(),
                kuerzel=kuerzel.strip(),
                ects=int(ects),
                tutor=(tutor.strip() or None),
                pruefungsform=pruefungsform,
                plan_start=plan_start or None,
                plan_ende=plan_ende or None,
                start_datum=start_datum or None,
            )
            st.session_state["add_kurs__just_saved"] = True
            st.rerun()
        except Exception as ex:
            st.error(f"❌ Speichern fehlgeschlagen: {ex}")


@st.dialog("Prüfung abgeben")
def submit_pruefung_dialog(service: FortschrittService, current_student_id: Optional[int]):
    """Dialog zum Abgeben einer Prüfung."""
    st.caption("📝 Kurs wählen und Abgabedatum setzen")
    

    # Kurse laden, die aktiv sind & noch nicht eingereicht
    # Erwartet: Liste von Objekten mit id, name, kurs_kuerzel (optional)
    kurse = getattr(service, "kurse_fuer_pruefungsabgabe", lambda sid: [])(current_student_id)

    # Optionen bauen (Label → ID)
    options = []
    values = []
    for k in kurse:
        kuerzel = getattr(k, "kurs_kuerzel", None) or getattr(k, "kuerzel", None) or ""
        label = f"{kuerzel+' – ' if kuerzel else ''}{getattr(k, 'name', 'Kurs')}"
        options.append(label)
        values.append(getattr(k, "id", None))

    if not options:
        st.info("Keine aktiven Kurse vorhanden, die eingereicht werden können.")
    else:
        # Selectbox zeigt Label, wir halten parallel den Kurs-ID-Wert
        idx = st.selectbox("**Kurs***", list(range(len(options))), format_func=lambda i: options[i], key="submit_kurs_idx")
        kurs_id = values[idx]

        abgabe = st.date_input("**Abgabedatum***", value=date.today(), key="submit_abgabe")

        st.divider()
        col_cancel, col_save = st.columns([1, 1])
        
        if col_cancel.button("❌ Abbrechen", use_container_width=True):
            st.rerun()
        
        if col_save.button("📤 Abgeben", type="primary", use_container_width=True):
            if not current_student_id:
                st.error("Bitte zuerst einen Studenten auswählen/anlegen.")
                return
            
            try:
                service.pruefung_abgeben(
                    student_id=current_student_id,
                    kurs_id=int(kurs_id),
                    abgabe_datum=abgabe,
                )
                st.session_state["submit_pruefung__just_saved"] = True
                st.rerun()
            except Exception as ex:
                st.error(f"❌ Fehler beim Abgeben: {ex}")


@st.dialog("Bewertung eintragen")
def add_bewertung_dialog(service: FortschrittService, current_student_id: Optional[int]):
    """Dialog zum Eintragen einer Bewertung."""
    st.caption("⭐ Note für abgegebenen Kurs eintragen")
    
    kurs_id = st.number_input("**Kurs-ID***", min_value=1, step=1, key="dialog_grade_kurs_id")
    note = st.number_input(
        "**Note*** (1.0 - 5.0)", 
        min_value=1.0, 
        max_value=5.0, 
        step=0.1, 
        value=1.0,
        format="%.1f", 
        key="dialog_grade_note"
    )
    
    st.info("💡 **Hinweis:** 1.0 = sehr gut, 5.0 = nicht bestanden")

    st.divider()
    col_cancel, col_save = st.columns([1, 1])
    
    if col_cancel.button("❌ Abbrechen", use_container_width=True):
        st.rerun()
    
    if col_save.button("💾 Speichern", type="primary", use_container_width=True):
        if not current_student_id:
            st.error("Bitte zuerst einen Studenten auswählen/anlegen.")
            return
        
        try:
            p = service.note_fuer_kurs_eintragen(
                student_id=current_student_id,
                kurs_id=int(kurs_id),
                note=float(note),
            )
            st.session_state["add_bewertung__just_saved"] = True
            st.session_state["last_pruefung_info"] = {
                "versuch_nr": p.versuch_nr,
                "bestanden": p.bestanden
            }
            st.rerun()
        except Exception as ex:
            st.error(f"❌ Fehler beim Speichern: {ex}")


@st.dialog("Studium abschließen")
def finish_studium_dialog(service: FortschrittService, current_student_id: Optional[int]):
    """Dialog zum Abschließen des Studiums."""
    st.caption("🎓 Abschluss prüfen und Studium beenden")
    st.warning("⚠️ Voraussetzungen: ECTS erreicht + Abschlussprüfung bestanden")
    
    ects_required = st.number_input(
        "Erforderliche ECTS (optional)", 
        min_value=0, 
        max_value=360, 
        step=5, 
        value=180,
        key="dialog_finish_ects_req"
    )
    
    st.info("💡 Lasse das Feld bei 0, wenn keine Mindest-ECTS geprüft werden sollen.")

    st.divider()
    col_cancel, col_save = st.columns([1, 1])
    
    if col_cancel.button("❌ Abbrechen", use_container_width=True):
        st.rerun()
    
    if col_save.button("✅ Prüfen & Abschließen", type="primary", use_container_width=True):
        if not current_student_id:
            st.error("Bitte zuerst einen Studenten auswählen/anlegen.")
            return
        
        try:
            ok = service.studium_abschliessen(
                student_id=current_student_id,
                erforderliche_ects=int(ects_required) if ects_required > 0 else None,
            )
            if ok:
                st.session_state["finish_studium__success"] = True
                st.rerun()
            else:
                st.warning("❌ Bedingungen noch nicht erfüllt (ECTS/Abschlussprüfung).")
        except Exception as ex:
            st.error(f"❌ Fehler: {ex}")


@st.dialog("Einstellungen")
def settings_dialog(current_student_id: Optional[int]):
    """Dialog für Einstellungen."""
    st.caption("⚙️ Anwendungseinstellungen")
    
    st.info("Hier kannst du später Einstellungen vornehmen:")
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
    service: FortschrittService,
    students: StudentRepository,
    current_student_id: Optional[int],
) -> None:
    """Eine Zeile, 5 Spalten – jeder Button öffnet einen eigenen Dialog."""
    
    # Toast-Nachrichten für erfolgreiche Aktionen
    if st.session_state.get("add_kurs__just_saved", False):
        st.session_state["add_kurs__just_saved"] = False
        st.toast("✅ Kurs erfolgreich gespeichert!")
    
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
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("➕ Kurs hinzufügen", use_container_width=True, key="open_add_kurs"):
            st.session_state["show_add_kurs_dialog"] = True
    
    with col2:
        if st.button("📝 Prüfung abgeben", use_container_width=True, key="open_submit_pruefung"):
            st.session_state["show_submit_pruefung_dialog"] = True
    
    with col3:
        if st.button("⭐ Bewertung eintragen", use_container_width=True, key="open_add_bewertung"):
            st.session_state["show_add_bewertung_dialog"] = True
    
    with col4:
        if st.button("🎓 Studium abschließen", use_container_width=True, key="open_finish_studium"):
            st.session_state["show_finish_studium_dialog"] = True
    
    with col5:
        if st.button("⚙️ Einstellungen", use_container_width=True, key="open_settings"):
            st.session_state["show_settings_dialog"] = True

    # Dialoge aufrufen, wenn entsprechende Flags gesetzt sind
    if st.session_state.get("show_add_kurs_dialog", False):
        st.session_state["show_add_kurs_dialog"] = False
        add_kurs_dialog(service, current_student_id)
    
    if st.session_state.get("show_submit_pruefung_dialog", False):
        st.session_state["show_submit_pruefung_dialog"] = False
        submit_pruefung_dialog(service, current_student_id)
    
    if st.session_state.get("show_add_bewertung_dialog", False):
        st.session_state["show_add_bewertung_dialog"] = False
        add_bewertung_dialog(service, current_student_id)
    
    if st.session_state.get("show_finish_studium_dialog", False):
        st.session_state["show_finish_studium_dialog"] = False
        finish_studium_dialog(service, current_student_id)
    
    if st.session_state.get("show_settings_dialog", False):
        st.session_state["show_settings_dialog"] = False
        settings_dialog(current_student_id)