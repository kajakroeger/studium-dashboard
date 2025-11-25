import streamlit as st


# Hauptfunktion -----------------------------------------------------
def render_debug_info(service, students, student_id, studiengang_id):
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
            if st.checkbox("Student"):
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
                studiengaenge = service.studiengaenge_fuer_student(student_id)
                if studiengaenge:
                    st.write(f"Gefundene Studiengänge: {len(studiengaenge)}")
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
                enrs = service.einschreibungen_fuer_student(student_id)  # Liste!
                if enrs:
                    st.write(f"Gefunden: {len(enrs)}")
                    st.json([
                        {
                            "id":            getattr(e, "id", None),
                            "student_id":    getattr(e, "student_id", None),
                            "studiengang_id":getattr(e, "studiengang_id", None),
                            "status":        str(getattr(e, "status", None)),
                            "start_datum":   getattr(e, "start_datum", None),
                            "ziel_enddatum": getattr(e, "ziel_enddatum", None),
                            "ziel_notenschnitt": getattr(e, "ziel_notenschnitt", None),
                            "end_datum":     getattr(e, "end_datum", None),
                            "abschluss_note":getattr(e, "abschluss_note", None),
                        }
                        for e in enrs
                    ])
                else:
                    st.warning("Für diesen Studenten wurden keine Einschreibungen gefunden.")


            # ---------- Kurse ----------
            if st.checkbox("Kurse"):
                kurse = service.kurse_all()
                if kurse:
                    st.write(f"Gefunden: {len(kurse)}")
                    st.json([
                        {
                            "id": k.id,
                            "name":k.name,
                            "kurs_kuerzel": k.kurs_kuerzel,
                            "ects": k.ects,
                            "tutor": k.tutor,
                            "semester": k.semester
                        }
                        for k in kurse
                    ])
                else:
                    st.warning("Keine Kurse gefunden")

            # ---------- Bearbeitungen ----------
            if st.checkbox("Bearbeitungen"):
                bearb = service.bearbeitungen_fuer_student(student_id)
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
            if st.checkbox("Prüfungen", key=f"debug_noten_{student_id}"):
                bearbeitungen = getattr(service, "bearbeitungen_fuer_student", lambda _sid: [])(student_id)
                rows = []

                # Wir nutzen hier die Prüfungs-Repo-Funktion über den Workflow
                pruef_repo = getattr(service._workflow, "_pruef", None)

                if pruef_repo is not None and hasattr(pruef_repo, "get_by_bearbeitung_id"):
                    for b in bearbeitungen:
                        p = pruef_repo.get_by_bearbeitung_id(getattr(b, "id", None))
                        if p:
                            rows.append(
                                {
                                    "bearbeitung_id": b.id,
                                    "kurs_id": b.kurs_id,
                                    "note": p.note,
                                    "bestanden": p.bestanden,
                                    "type_bestanden": type(p.bestanden).__name__,
                                    "versuch_nr": p.versuch_nr,
                                    "letzter_versuch": p.letzter_versuch,
                                }
                            )
                st.write(rows)


        except Exception as ex:
            st.error(f"Debug-Fehler: {ex}")
