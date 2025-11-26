# core/workflow_service.py
from __future__ import annotations
from datetime import date
from typing import Optional, List, Tuple

from models.student import Student
from models.bearbeitung import Bearbeitung, StatusBearbeitung
from models.einschreibung import Einschreibung, StatusEinschreibung
from models.studiengang import Studiengang
from models.kurs import Kurs
from models.pruefung import Pruefung, Pruefungsform


class WorkflowService:
    def __init__(
        self,
        *,
        student_repo,
        bearbeitung_repo,
        kurs_repo,
        pruefung_repo,
        einschreibung_repo,
        studiengang_repo,
        ects_summe_bestanden_fn,
        notenschnitt_fn,
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo
        self._studiengang_repo = studiengang_repo
        self._ects_summe_bestanden_fn = ects_summe_bestanden_fn
        self._notenschnitt_fn = notenschnitt_fn


    # ---------------- CRUD/Workflows (Delegation) ---------------- 
    # ---------------- STUDENT ---------------- 
    def create_student(
        self,
        *,
        name: str,
        matrikelnummer: str,
        email: Optional[str],
        uni_email: Optional[str],
        ziel_notenschnitt: float,
        ziel_enddatum: date,
        # studiengang_id: Optional[int] = None,
        studiengang_name: Optional[str] = None,
        studiengang_monate: Optional[int] = None,
        studiengang_kurse: Optional[int] = None,
        studiengang_ects: Optional[int] = None,
    ) -> int:
        print(f"Erstelle neuen Studenten für {name}…")
        
        # 1) Student anlegen
        student = Student(
            name=name,
            matrikelnummer=matrikelnummer,
            email=email,
            uni_email=uni_email,
        )
        student_id = int(self._students.create(student))
        print(f"Student erstellt mit ID: {student_id}")

        # 2) Studiengang-ID abrufen und Studiengang anlegen 
        sg_id = self._ensure_studiengang(
            name=studiengang_name,
            anzahl_monate=studiengang_monate,
            anzahl_kurse=studiengang_kurse,
            ects_gesamt=studiengang_ects,
        )
        print(f"Studiengang erstellt, Studiengang-ID: {sg_id}")

        # 3) Einschreibung mit Zielen speichern
        eins = Einschreibung(
            student_id=student_id,
            start_datum=date.today(),
            ziel_enddatum=ziel_enddatum,
            ziel_notenschnitt=ziel_notenschnitt,
            status=StatusEinschreibung.AKTIV,
            studiengang_id=sg_id,
        )
        try:
            einschreibung_id = self._einschreibungen.create(eins)
            print(f"✅ Einschreibung erstellt mit ID: {einschreibung_id}")
        except Exception as e:
            print(f"❌ FEHLER beim Erstellen der Einschreibung: {e}")
            import traceback
            traceback.print_exc()
            raise
        return student_id
    

    def student_by_id(self, student_id: int) -> Optional[Student]:
        """Gibt den Studenten mit der angegebenen ID zurück."""
        return self._students.get_by_id(student_id)
    
    def student_all(self) -> List[Student]:
        """Gibt alle Studenten als Liste zurück."""
        return list(self._students.all())
    


    # ---------------- STUDIENGANG ----------------             
    def studiengang_by_id(self, studiengang_id: Optional[int]):
        """Gibt den Studiengang mit der angegebenen ID zurück (oder None)."""
        if not studiengang_id:
            return None
        try:
            sg_id = int(studiengang_id)
        except Exception:
            return None

        # bevorzugte Getter im Repo
        getter = (getattr(self._studiengang_repo, "get_by_id", None)
                  or getattr(self._studiengang_repo, "get", None))
        if callable(getter):
            return getter(sg_id)

        # Fallback über all() (falls es keinen direkten Getter gibt)
        all_fn = getattr(self._studiengang_repo, "all", None)
        if callable(all_fn):
            for sg in all_fn() or []:
                if getattr(sg, "id", None) == sg_id:
                    return sg

        return None   
    

    def studiengang_by_name(self, name: str):
        """Gibt den Studiengang mit dem angegebenen Namen zurück."""
        if not name:
            return None
        return self._studiengang_repo.get_by_name(name)
    
    def studiengaenge_fuer_student(self, student_id: int):
        """Gibt alls Studiengänge, in die ein Student eingeschrieben ist"""
        einschreibungen = self.einschreibungen_fuer_student(student_id)
        studiengang_ids = [getattr(e, "studiengang_id", None) for e in einschreibungen if getattr(e, "studiengang_id", None)]
        result = []
        for studiengang_id in studiengang_ids:
            studiengang = self.studiengang_by_id(studiengang_id)
            if student_id:
                result.append(studiengang)
        return result

    def studiengang_all(self):
        """Gibt alle Studiengänge zurück."""
        return list(self._studiengang_repo.all())



    # ---------------- EINSCHREIBUNGEN ----------------    
    def einschreibungen_fuer_student(self, student_id: int):
        if hasattr(self._einschreibungen, "einschreibungen_fuer_student"):
            return list(self._einschreibungen.einschreibungen_fuer_student(student_id) or [])
        # if hasattr(self._einschreibungen, "all"):
        #     return [e for e in self._einschreibungen.all() if getattr(e, "student_id", None) == student_id]
        return []
    
    
    def aktive_einschreibung(self, student_id: int):
        """Gibt die aktive Einschreibung eines Studenten zurück."""
        if not student_id:
            return None
        
        try:
            student_id = int(student_id)
        except (ValueError, TypeError):
            return None
        
        return self._einschreibungen.get_aktive_fuer_student(student_id)
    


    # ---------------- KURSE ----------------    
    def kurse_all(self):
        if hasattr(self._kurse, "all"):
            return list(self._kurse.all() or [])
        return []

    def kurs_by_id(self, kurs_id: int):
        if hasattr(self._kurse, "get"):
            return self._kurse.get(kurs_id)
        if hasattr(self._kurse, "get_by_id"):
            return self._kurse.get_by_id(kurs_id)
        return None

    def kurs_name_exists(self, name: str) -> bool:
        return bool(getattr(self._kurse, "exists_by_name", lambda _n: False)((name or "").strip()))

    def kurs_kuerzel_exists(self, kurs_kuerzel: str) -> bool:
        return bool(getattr(self._kurse, "exists_by_kuerzel", lambda _k: False)((kurs_kuerzel or "").strip()))



    def kurse_fuer_pruefungsabgabe(
            self,
            student_id: int,
            studiengang_id: Optional[int] = None,
            debug: bool = False,
        ) -> List[Kurs]:
        """
        Liefert alle Kurse, für die der Student aktuell eine Prüfung abgeben kann.

        Regeln:
        - Bearbeitung gehört zum Studenten (+ optional Studiengang)
        - Status 'aktiv' (Enum oder String)
        - noch KEIN Abgabedatum
        """

        # 1) Bearbeitungen & Kurse über den Service holen
        bearb_list: List[Bearbeitung] = list(self.bearbeitungen_fuer_student(student_id) or [])
        alle_kurse = {k.id: k for k in (self.kurse_all() or [])}

        kurse: List[Kurs] = []
        debug_rows = []

        for b in bearb_list:
            # Status robust in Text umwandeln (Enum ODER String)
            status_raw = getattr(b, "status", "")
            status_val = getattr(status_raw, "value", status_raw)   # <- wichtig für Enum
            status_txt = str(status_val).strip().lower()

            # Abgabedatum robust behandeln (kann None, "", str oder date sein)
            abgabe_raw = getattr(b, "abgabe_datum", None)
            abgabe = self._to_date(abgabe_raw) if hasattr(self, "_to_date") else abgabe_raw

            row = {
                "bearbeitung_id": getattr(b, "id", None),
                "kurs_id": getattr(b, "kurs_id", None),
                "status_raw": status_raw,
                "status_norm": status_txt,
                "abgabe_datum_raw": abgabe_raw,
                "abgabe_datum_parsed": abgabe,
                "geht_in_auswahl": False,
                "grund": "",
            }

            # optional: Studiengang filtern, falls vorhanden
            if studiengang_id is not None:
                b_sg = getattr(b, "studiengang_id", None)
                if b_sg not in (None, studiengang_id):
                    row["grund"] = f"falscher Studiengang ({b_sg})"
                    debug_rows.append(row)
                    continue

            # Regel 1: nur "aktiv"
            if not status_txt.startswith("aktiv"):
                row["grund"] = f"Status nicht aktiv ('{status_txt}')"
                debug_rows.append(row)
                continue

            # Regel 2: nur ohne Abgabedatum
            if abgabe is not None:
                row["grund"] = f"hat bereits Abgabedatum ({abgabe})"
                debug_rows.append(row)
                continue

            # Kurs zuordnen
            kurs = alle_kurse.get(getattr(b, "kurs_id", None))
            if kurs is None:
                row["grund"] = f"kein Kurs mit id={getattr(b, 'kurs_id', None)} gefunden"
                debug_rows.append(row)
                continue

            # alles OK → Kurs aufnehmen
            row["geht_in_auswahl"] = True
            row["grund"] = "OK"
            debug_rows.append(row)
            kurse.append(kurs)

        # Debug im Service ablegen
        self._debug_kurse_fuer_pruefungsabgabe = debug_rows

        if debug:
            print("DEBUG kurse_fuer_pruefungsabgabe Entscheidungen:")
            for r in debug_rows:
                print(r)
            print("Kurse in Auswahl:", [k.id for k in kurse])

        return kurse


    # ---------------- BEARBEITUNGEN ----------------    
    def bearbeitungen_fuer_student(self, student_id: int):
        for fn in ("list_by_student", "einschreibungen_fuer_student"):
            if hasattr(self._bearb, fn):
                return list(getattr(self._bearb, fn)(student_id) or [])
        return []
    


    # ---------------- Action Bar Acktion: Kurs hinzufügen ----------------
    def add_kurs_mit_bearbeitung_und_pruefung(
        self,
        *,
        student_id: int,
        name: str,
        kurs_kuerzel: str,
        ects: int,
        tutor: Optional[str] = None,
        pruefungsform: Optional[Pruefungsform] = None,
        plan_start: Optional[date] = None,
        plan_end: Optional[date] = None,
        start_datum: Optional[date] = None,
    ) -> int:
        name_clean = (name or "").strip()
        ku_clean = (kurs_kuerzel or "").strip()
        if not name_clean or not ku_clean:
            raise ValueError("Name und Kurskürzel dürfen nicht leer sein.")
        if int(ects) <= 0:
            raise ValueError("ECTS muss > 0 sein.")

        if getattr(self._kurse, "exists_by_name", None) and self._kurse.exists_by_name(name_clean):
            raise ValueError(f"Ein Kurs mit dem Namen '{name_clean}' existiert bereits.")
        if getattr(self._kurse, "exists_by_kuerzel", None) and self._kurse.exists_by_kuerzel(ku_clean):
            raise ValueError(f"Ein Kurs mit dem Kürzel '{ku_clean}' existiert bereits.")

        kurs = Kurs(
            name=name_clean,
            kurs_kuerzel=ku_clean,
            ects=int(ects),
            tutor=(tutor.strip() or None) if tutor else None,
            semester=0,
        )
        kurs_id = int(self._kurse.create(kurs))

        status = StatusBearbeitung.AKTIV if start_datum else StatusBearbeitung.INAKTIV
        bearb = Bearbeitung(
            kurs_id=kurs_id,
            student_id=student_id,
            start_datum=start_datum,
            plan_start=plan_start,
            plan_end=plan_end,
            status=status,
        )
        bearbeitung_id = int(self._bearb.create(bearb))

        if pruefungsform is not None:
            pruef = Pruefung(
                bearbeitung_id=bearbeitung_id,
                pruefungsform=pruefungsform,
                note=None,
                versuch_nr=0,
                bestanden=False,
            )
            self._pruef.create(pruef)

        return kurs_id



    # ---------------- Action Bar Acktion: Kurs starten ----------------
    def bearbeitung_starten(self, bearbeitung_id: int, start_datum: date) -> None:
        b = self._bearb.get_by_id(bearbeitung_id)
        if not b:
            raise ValueError(f"Bearbeitung {bearbeitung_id} nicht gefunden")

        b.start_datum = start_datum
        # Status ggf. auf "aktiv" setzen, wenn dein Enum das hat
        if hasattr(b, "status"):
            from models.bearbeitung import StatusBearbeitung
            try:
                b.status = StatusBearbeitung.AKTIV
            except Exception:
                pass

        self._bearb.update(b)


    # ---------------- Action Bar Acktion: Prüfung abgeben ----------------
    def pruefung_abgeben(self, student_id: int, kurs_id: int, abgabe_datum: date):
        bearbeitungen = list(self.bearbeitungen_fuer_student(student_id) or [])
        passende = [b for b in bearbeitungen if getattr(b, "kurs_id", None) == kurs_id]
        if not passende:
            raise ValueError("…")
        b = passende[0]
        b.abgabe_datum = abgabe_datum
        self._bearb.update(b)
        return b
    

    # ---------------- Action Bar Acktion: Bewertung eintragen ----------------
    def note_fuer_kurs_eintragen(
        self,
        *,
        student_id: int,
        kurs_id: int,
        note: float,
    ) -> Pruefung:
        """
        Trägt eine Note für einen Kurs ein.

        Fachlogik:
        - es wird die Bearbeitung des Studenten mit Abgabedatum verwendet
        - Note 1.0–4.0 -> bestanden = True, Bearbeitung -> ABGESCHLOSSEN
        - Note > 4.0 -> bestanden = False, Bearbeitung bleibt AKTIV
        - Versuchszähler wird pro Eintrag hochgezählt
        (3.-Versuch-Logik fürs Studium kannst du hier später ergänzen)
        """

        # 1) passende Bearbeitung finden (mit Abgabedatum)
        bearb = self._bearb.fuer_student_und_kurs_mit_abgabe(student_id, kurs_id)
        if bearb is None:
            raise ValueError(
                "Es gibt keine Bearbeitung mit Abgabedatum für diesen Kurs. "
                "Bitte zuerst die Prüfung abgeben."
            )

        bestanden = 1.0 <= float(note) <= 4.0

        # 2) bestehende Prüfung zu dieser Bearbeitung laden
        pruefung = self._pruef.get_by_bearbeitung_id(bearb.id)

        if pruefung is None:
            # 2a) erste Bewertung für diese Bearbeitung
            pruefung = Pruefung(
                id=None,
                bearbeitung_id=bearb.id,
                kurs_id=kurs_id,
                pruefungsform=None,   # oder vorhandene Logik, falls du eine Form speichern willst
                note=float(note),
                versuch_nr=1,
                bestanden=bestanden,
                letzter_versuch=False,  # kannst du später setzen, wenn du 3-Versuchs-Logik einbaust
            )
            self._pruef.create(pruefung)
        else:
            # 2b) weitere Versuche / Noten-Update
            pruefung.note = float(note)
            pruefung.versuch_nr = (pruefung.versuch_nr or 0) + 1
            pruefung.bestanden = bestanden
            # letzter_versuch kannst du z.B. bei Versuch 3 setzen
            self._pruef.update(pruefung)

        # 3) Bearbeitungs-Status anpassen
        if bestanden:
            bearb.status = StatusBearbeitung.ABGESCHLOSSEN
            self._bearb.update(bearb)
        else:
            # bei Nicht-Bestehen bleibt die Bearbeitung aktiv
            # (3.-Versuch-Logik könntest du hier ergänzen)
            pass

        return pruefung
    
    def offene_kurse_fuer_bewertung(
        self,
        student_id: int,
    ) -> List[Tuple[Bearbeitung, Kurs, Optional[Pruefung]]]:
        """
        Liefert alle Bearbeitungen/Kurse, für die eine Note eingetragen werden kann.

        Kriterien:
        - Bearbeitung gehört zum Studenten
        - status == PRUEFUNG_EINGEREICHT
        - abgabe_datum ist gesetzt
        """

        bearbeitungen = self.bearbeitungen_fuer_student(student_id)
        result: List[Tuple[Bearbeitung, Kurs, Optional[Pruefung]]] = []
        debug_rows = []

        for b in bearbeitungen:
            abgabe = getattr(b, "abgabe_datum", None)
            status = getattr(b, "status", None)

            row = {
                "bearbeitung_id": getattr(b, "id", None),
                "kurs_id": getattr(b, "kurs_id", None),
                "status": str(status),
                "abgabe_datum": abgabe,
                "offen": False,
                "grund": "",
            }

            # 1) Status muss PRUEFUNG_EINGEREICHT sein
            if status is not StatusBearbeitung.PRUEFUNG_EINGEREICHT:
                row["grund"] = f"Status nicht PRUEFUNG_EINGEREICHT ({status})"
                debug_rows.append(row)
                continue

            # 2) Abgabedatum muss gesetzt sein
            if not abgabe:
                row["grund"] = "kein abgabe_datum gesetzt"
                debug_rows.append(row)
                continue

            # 3) Kurs holen
            kurs: Optional[Kurs] = self._kurse.get_by_id(b.kurs_id)
            if not kurs:
                row["grund"] = "kein Kurs gefunden"
                debug_rows.append(row)
                continue

            # Optional: aktuelle Prüfung holen (falls schon einer bewertet wurde)
            pruefung: Optional[Pruefung] = self._pruef.get_by_bearbeitung_id(b.id)

            row["grund"] = "OK"
            row["offen"] = True
            debug_rows.append(row)

            result.append((b, kurs, pruefung))

        # Debug-Infos für UI
        self._debug_offene_bewertungen = debug_rows
        return result


    def _behandle_dritten_fehlversuch(self, student_id: int) -> None:
        """
        Konsequenzen beim dritten Fehlversuch:
        z.B. Einschreibung auf 'beendet/nicht bestanden' setzen.
        Hier implementierst du genau das, was dein Modell vorsieht.
        """
        einschreibung = self._einschreibungen.aktive_einschreibung_fuer_student(student_id)
        if einschreibung:
            einschreibung.status = "beendet_nicht_bestanden"  # oder Enum
            self._einschreibungen.update(einschreibung)
    


    # ---------------- Action Bar Acktionen: Studium abschließen ----------------
    def studium_abschliessen(self, *, student_id: int, erforderliche_ects: Optional[int] = None) -> bool:
        if erforderliche_ects is not None:
            if self._ects_summe_bestanden_fn(student_id) < erforderliche_ects:
                return False

        bearb_list: List[Bearbeitung] = []
        for fn in ("einschreibungen_fuer_student", "list_by_student"):
            if hasattr(self._bearb, fn):
                bearb_list = list(getattr(self._bearb, fn)(student_id) or [])
                break

        for b in bearb_list:
            pruef = getattr(self._pruef, "get_by_bearbeitung_id", lambda _id: None)(b.id)
            if not pruef or not getattr(pruef, "bestanden", False):
                return False

        eins = getattr(self._einschreibungen, "get_aktive_fuer_student", lambda _sid: None)(student_id)
        if eins:
            notenschnitt = self._notenschnitt_fn(student_id) if callable(self._notenschnitt_fn) else 0.0
            eins.abschliessen(enddatum=date.today(), notenschnitt=notenschnitt)
            self._einschreibungen.update(eins)
        return True




    # ---------------- KPIs / Fortschritt ---------------
    def hole_studienziele(self, student_id: int):
        return self._goals.hole_studienziele(student_id)
    

    # TODO: ist in der FortschrittService angegeben, muss aber noch definiert werfden 
    def berechne_ziel_status(self, student_id: int):
        return self._goals.berechne_ziel_status(student_id)

    

    # ---------------- interne Hilfsmethoden ---------------- 
    # Prüft, ob Studiengang existiert, wenn nicht wird einer erstellt 
    def _ensure_studiengang(
        self,
        *,
        name: Optional[str],
        anzahl_monate: Optional[int],
        anzahl_kurse: Optional[int],
        ects_gesamt: Optional[int],
    ) -> int:
        """
        Liefert eine Studiengang-ID.
        Erstellt einen neuen Studiengang, falls nötig.
        """
        if not name or anzahl_monate is None or anzahl_kurse is None or ects_gesamt is None:
            raise ValueError("Studiengangdaten unvollständig (Name/Monate/Kurse/ECTS).")

        # Prüfen, ob Studiengang bereits existiert
        existing = self._studiengang_repo.get_by_name(name)
        if existing and existing.id is not None:
            print(f"✅ Studiengang '{name}' existiert bereits mit ID: {existing.id}")
            return existing.id

        # Neuen Studiengang anlegen
        from models.studiengang import Studiengang
        sg = Studiengang(
            name=name,
            anzahl_monate=int(anzahl_monate),
            anzahl_kurse=int(anzahl_kurse),
            ects_gesamt=int(ects_gesamt),
        )
        sg_id = self._studiengang_repo.create(sg)
        print(f"✅ Neuer Studiengang '{name}' erstellt mit ID: {sg_id}")
        return sg_id