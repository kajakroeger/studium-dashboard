# streamlit run ui/streamlit_dashboard_ui.py

"""
Datei: ui/streamlit_dashboard_ui.py
Beschreibung:
Streamlit-UI für das Studium-Dashboard.
- Zeigt beim ersten Start ein Onboarding-Modal (Student + Studienziele)
- Nutzt den FortschrittService (Application Layer) für alle Berechnungen
- Bleibt austauschbar dank UIAdapter-Schnittstelle

Start (vom Projektroot):
    pip install streamlit pandas
    streamlit run ui/streamlit_dashboard_ui.py

Optional: DB-Pfad per Flag:
    streamlit run ui/streamlit_dashboard_ui.py -- --db studium.db
"""

from __future__ import annotations

from typing import Optional


import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import streamlit as st
st.sidebar.caption(f"Streamlit: v{getattr(st, '__version__', 'unknown')} {getattr(st, '__file__', 'n/a')}")

# Fachservice & Ports (keine DB-/UI-Details)
from core import FortschrittService
from db import SQLiteConnectionProvider

# Repositories (SQLite-Impls)
from db.repositories.student_repository import StudentRepository
from db.repositories.sqlite_student_repository import SQLiteStudentRepository
from db.repositories.sqlite_bearbeitung_repository import SQLiteBearbeitungRepository
from db.repositories.sqlite_kurs_repository import SQLiteKursRepository
from db.repositories.sqlite_pruefung_repository import SQLitePruefungRepository
from db.repositories.sqlite_einschreibung_repository import SQLiteEinschreibungRepository

# UI-Adapter (Interface)
from ui.ui_adapter import UIAdapter


class StreamlitDashboardUI(UIAdapter):
    """
    Streamlit-Implementierung der UI.
    Nutzt:
      - FortschrittService: liefert fertige DTOs für die Anzeige
      - StudentRepository: um die Auswahlbox zu befüllen
    """

    def __init__(self, service: FortschrittService, student_repo: StudentRepository) -> None:
        self._service = service
        self._students = student_repo

    # ---------------------------------------------------------
    # Öffentliche API (UIAdapter)
    # ---------------------------------------------------------

    def zeige_dashboard(self) -> None:
        """Rendert das komplette Dashboard in Streamlit."""
        st.set_page_config(page_title="Studium Dashboard", page_icon="🎓", layout="wide")
        st.title("🎓 Studium Dashboard")

        # --- Onboarding: Wenn noch kein Student existiert, zeige Dialog und beende Rendering ---
        alle = list(self._students.all())
        if not alle:
            self._show_onboarding_dialog()
            st.info("Bitte lege zuerst einen Studenten an.")
            return

        # --- Sidebar: Studentenauswahl ---
        st.sidebar.header("Auswahl")
        student_id = self._student_selectbox()
        if student_id is None:
            st.info("Bitte wähle einen Studenten in der Sidebar aus.")
            return

        # --- Daten laden (Fachlogik im Service) ---
        try:
            uebersicht = self._service.gesamtuebersicht(student_id)
        except ValueError as ex:
            st.error(str(ex))
            return

        # --- KPI-Kacheln (entsprechend Wireframe) ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("ECTS (bestanden)", uebersicht.ects_bestanden)
        col2.metric("ECTS (gesamt bekannt)", uebersicht.ects_gesamt_bekannt)
        col3.metric("ø-Note", "—" if uebersicht.notenschnitt is None else f"{uebersicht.notenschnitt:.2f}")
        col4.metric(
            "Abgeschlossen / Offen",
            f"{uebersicht.anzahl_bearbeitungen_abgeschlossen} / {uebersicht.anzahl_bearbeitungen_offen}",
        )

        st.markdown("---")

        # --- Kurse (Tabelle) ---
        st.subheader("📚 Kurse")
        df_kurse = pd.DataFrame(
            [
                {
                    "Kurs-ID": k.kurs_id,
                    "Kurs": k.kurs_name,
                    "ECTS": k.ects,
                    "Bestanden": _fmt_bool(k.bestanden),
                    "Note": k.note,
                    "Versuch": k.versuch_nr,
                    "Letzter Versuch": _fmt_bool(k.letzter_versuch),
                }
                for k in uebersicht.kurse
            ]
        )
        st.dataframe(df_kurse, use_container_width=True)

        # --- Bearbeitungen (Tabelle) ---
        st.subheader("🧩 Bearbeitungen")
        df_bearb = pd.DataFrame(
            [
                {
                    "Bearbeitung-ID": b.bearbeitung_id,
                    "Kurs-ID": b.kurs_id,
                    "Status": b.status.value,
                    "Tage in Bearbeitung": b.tage_bearbeitung,
                    "Prüfung bestanden": _fmt_bool(b.pruefung_bestehen),
                    "Note": b.pruefung_note,
                    "Versuch": b.pruefung_versuch,
                    "Letzter Versuch": _fmt_bool(b.pruefung_letzter_versuch),
                }
                for b in uebersicht.bearbeitungen
            ]
        )
        st.dataframe(df_bearb, use_container_width=True)

        # --- (Optional) Aktion: Note eintragen ---
        with st.expander("✍️ Note eintragen (Demo)"):
            self._note_eintragen_form()

    # ---------------------------------------------------------
    # Private UI-Hilfen
    # ---------------------------------------------------------

    def _student_selectbox(self) -> Optional[int]:
        """Zeigt eine Selectbox mit allen Studenten und gibt die ID zurück (oder None)."""
        alle = list(self._students.all())
        if not alle:
            return None

        # Anzeige-Label und Mapping Index -> Objekt
        labels = [f"{s.id} – {getattr(s, 'name', str(s))}" for s in alle]
        selected_index = st.sidebar.selectbox(
            "Student", options=list(range(len(alle))), format_func=lambda i: labels[i]
        )
        return alle[selected_index].id

    def _note_eintragen_form(self) -> None:
        """Kleines Formular, um eine Note für eine Bearbeitung einzutragen (Demo)."""
        col1, col2 = st.columns([2, 1])
        bearbeitung_id = col1.number_input("Bearbeitung-ID", min_value=1, step=1)
        note = col2.number_input("Note (z. B. 1.7)", min_value=1.0, max_value=5.0, step=0.1, format="%.1f")
        if st.button("Note speichern"):
            try:
                p = self._service.trage_note_ein(int(bearbeitung_id), float(note))
                st.success(f"Note gespeichert. Versuch #{p.versuch_nr}, bestanden={p.bestanden}.")
            except Exception as ex:
                st.error(f"Fehler: {ex}")

    def _show_onboarding_dialog(self) -> None:
        """
        Zeigt ein Formular, um Student + Studienziele anzulegen.
        Nutzt st.modal, fällt auf st.dialog oder st.expander zurück, wenn nötig.
        """
        import streamlit as st

        st.warning("Keine Studenten gefunden. Lege zuerst Datensätze an.")

        def _form_content() -> None:
            st.write("Bitte gib deine Daten und Studienziele ein.")
            with st.form("onboarding_form", clear_on_submit=False):
                name = st.text_input("Voller Name *", placeholder="z. B. Kaja Kröger")
                matrikel = st.text_input("Matrikelnummer *", placeholder="z. B. A-12345")
                email = st.text_input("E-Mail (optional)")
                uni_email = st.text_input("Uni-E-Mail (optional)")

                col1, col2 = st.columns(2)
                ziel_noten = col1.number_input(
                    "Ziel-Notenschnitt *", min_value=1.0, max_value=5.0, step=0.1, format="%.1f"
                )
                ziel_end = col2.date_input("Zieldatum Bachelorarbeit *")

                submitted = st.form_submit_button("Speichern")
                if submitted:
                    if not name or not matrikel:
                        st.error("Name und Matrikelnummer sind Pflichtfelder.")
                    else:
                        try:
                            self._service.create_student(
                                name=name,
                                matrikelnummer=matrikel,
                                email=email or None,
                                uni_email=uni_email or None,
                                ziel_notenschnitt=float(ziel_noten),
                                ziel_enddatum=ziel_end,
                            )
                            st.success("Gespeichert! Dashboard wird aktualisiert …")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Fehler beim Anlegen: {ex}")

        # Feature-Detection: modal → dialog → expander
        if hasattr(st, "modal"):
            with st.modal("Willkommen 👋 – Lass uns starten!"):
                _form_content()
        elif hasattr(st, "dialog"):
            @st.dialog("Willkommen 👋 – Lass uns starten!")
            def _dlg():
                _form_content()
            _dlg()
        else:
            with st.expander("👋 Willkommen – Lass uns starten!", expanded=True):
                _form_content()



# ---------------------------------------------------------
# Composition Root (nur für Streamlit-Standalone)
# ---------------------------------------------------------

def _build_service(db_path: str = "studium.db") -> tuple[FortschrittService, StudentRepository]:
    """
    Baut den Service + Repositories zusammen (Zusammenschaltung/DI).
    Das ist *keine* Fachlogik, sondern reines Wiring.
    """
    provider = SQLiteConnectionProvider(db_path)
    student_repo = SQLiteStudentRepository(provider)
    bearb_repo = SQLiteBearbeitungRepository(provider)
    kurs_repo = SQLiteKursRepository(provider)
    pruefung_repo = SQLitePruefungRepository(provider)
    einschreibung_repo = SQLiteEinschreibungRepository(provider)

    service = FortschrittService(
        student_repo=student_repo,
        bearbeitung_repo=bearb_repo,
        kurs_repo=kurs_repo,
        pruefung_repo=pruefung_repo,
        einschreibung_repo=einschreibung_repo,
    )
    return service, student_repo


def _fmt_bool(value: Optional[bool]) -> str:
    """Darstellung für Ja/Nein/—."""
    if value is None:
        return "—"
    return "Ja" if value else "Nein"


# Streamlit-Einstiegspunkt
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="studium.db", help="Pfad zur SQLite-Datenbank")
    args = parser.parse_args()

    service, student_repo = _build_service(args.db)
    ui = StreamlitDashboardUI(service, student_repo)
    ui.zeige_dashboard()
