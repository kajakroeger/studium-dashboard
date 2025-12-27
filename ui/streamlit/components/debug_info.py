from typing import Optional
import streamlit as st


def render_debug_info(service, student_id, studiengang_id: Optional[int]):
    """
    Zeigt umfangreiche Debug-Infos zum gewählten Studenten an:
    - Studentendaten
    - Einschreibungen
    - Studiengang
    - Kurse, Bearbeitungen, Prüfungen
    """

    with st.expander("🔎 Debug (nur temporär)"):
        try:
            # ---------- Student ----------
            if st.checkbox("Alle Studenten"):
                student = service.student_by_id(student_id)
                if student:
                    st.json({
                        "id": student.id,
                        "name": student.name,
                        "matrikelnummer": student.matrikelnummer,
                        "email": student.email,
                        "uni_email": student.uni_email,
                    })
                else:
                    st.warning("Kein Student gefunden.")

            
            # ---------- Studiengang ----------
            if st.checkbox("Studiengang"):
                studiengaenge = service.studiengaenge_by_student_id(student_id)
                if studiengaenge:
                    st.write(f"Alle Studiengänge: {len(studiengaenge)}")
                    st.json([
                        {
                            "id:": sg.id,
                            "name": sg.name,
                            "anzahl_monate": sg.anzahl_monate,
                            "anzahl_kurse": sg.anzahl_kurse,
                            "ects_gesamt": sg.ects_gesamt,
                        }
                        for sg in studiengaenge
                    ])
                else:
                    st.warning("Für diesen Studenten wurden keine Studiengänge gefunden.")


            # ---------- Einschreibungen ----------
            if st.checkbox("Einschreibungen"):
                enrs = service.einschreibungen_fuer_student(student_id)  
                if enrs:
                    st.write(f"Alle Einschreibungen: {len(enrs)}")
                    st.json([
                        {
                            "id": e.id,
                            "student_id": e.student_id,
                            "studiengang_id": e.studiengang_id,
                            "status": e.status,
                            "start_datum": e.start_datum,
                            "ziel_enddatum": e.ziel_enddatum,
                            "ziel_notenschnitt": e.ziel_notenschnitt,
                            "end_datum": e.end_datum,
                            "abschluss_note": e.abschluss_note,
                        }
                        for e in enrs
                    ])
                else:
                    st.warning("Für diesen Studenten wurden keine Einschreibungen gefunden.")


            # ---------- Kurse ----------
            if st.checkbox("Kurse"):
                kurse = service.kurse_fuer_student(student_id, studiengang_id)

                if kurse:
                    st.write(f"Alle Kurse des aktuellen Studenten und ausgewählten Studiengangs: {len(kurse)}")
                    st.json([
                        {
                            "id": k.id,
                            "name": k.name,
                            "kurs_kuerzel": k.kurs_kuerzel,
                            "ects": k.ects,
                            "tutor": k.tutor,
                            "semester": k.semester,
                            "studiengang_id": k.studiengang_id,
                        }
                        for k in kurse
                    ])
                else:
                    st.warning("Keine Kurse gefunden")

            # ---------- Bearbeitungen ----------
            if st.checkbox("Alle Bearbeitungen des aktuellen Studenten und ausgewählten Studiengangs"):
                bearb = service.bearbeitungen_fuer_student(student_id, studiengang_id)
                if bearb:
                    st.write(f"Gefunden {len(bearb)}")
                    st.json([
                        {
                            "id": b.id,
                            "student_id": b.student_id,
                            "kurs_id": b.kurs_id,
                            "status": b.status,
                            "plan_start": b.plan_start,
                            "plan_end": b.plan_end,
                            "start_datum": b.start_datum,
                            "abgabe_datum": b.abgabe_datum,
                        }
                        for b in bearb
                    ])
                else:
                    st.warning("Keine Bearbeitungen gefunden")

            # ---------- Prüfungen ----------        
            if st.checkbox("Alle Prüfungen des aktuellen Studenten und ausgewählten Studiengangs"):
                pruefungen = service.pruefungen_fuer_student(student_id, studiengang_id)
                
                if pruefungen:
                    st.write(f"Gefundene Prüfungen: {len(pruefungen)}")
                    st.json([
                        {
                            "id": pruefung.id,
                            "kurs": kurs.name,
                            "pruefungsform": pruefung.pruefungsform,
                            "versuch_nr": pruefung.versuch_nr,
                            "note": pruefung.note,
                            "bestanden": pruefung.bestanden,
                            "letzter_versuch": pruefung.letzter_versuch,
                
                        }
                        for _, kurs, pruefung in pruefungen
                    ])
                else:
                    st.warning("Keine Prüfungen gefunden")

        except Exception as ex:
            st.error(f"Debug-Fehler: {ex}")
