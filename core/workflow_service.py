# core/workflow_service.py
from __future__ import annotations
from datetime import date
from typing import Iterable, List, Optional, Tuple

from core.dtos import AbgeschlosseneBearbeitung, StudiengangOption
from db.repositories import *
from models import *


class WorkflowService:
    """
    ↔️ KÜCHEN-LAGER-KOORDINATION
    - vermittelt zwischen Lager (DB) und Koch (ProgressService)
    - definiert, was und wann in welches Regal abgelegt oder genommen wird

    Technisch:
    Reine Domänenlogik & Datenzugriff. Kennt nur die Repositories. 
    Bietet Read-/Workflow-Methoden, aber keine Auswertungen (kein Notenschnitt, keine ECTS-Analysen usw.).
    
    Verantwortlich für:
    - Zugriff auf Stammdaten (Student, Kurs, Studiengang, Einschreibung)
    - Zugriff auf Bearbeitungen & Prüfungen
    - setzt Domänenregeln durch / validiert fachlich
    - einfache Workflow-Operationen (z. B. Kurs starten, Prüfung anlegen, etc.)
    """

    def __init__(
        self,
        *,
        student_repo: StudentRepository,
        bearbeitung_repo: BearbeitungRepository,
        kurs_repo: KursRepository,
        pruefung_repo: PruefungRepository,
        einschreibung_repo: EinschreibungRepository,
        studiengang_repo: StudiengangRepository,
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo
        self._studiengaenge = studiengang_repo

    # ---------------------------------------------------------------------
    # Onboarding
    # ---------------------------------------------------------------------

    def onboarding(
        self,
        *,
        student_name: str,
        matrikelnummer: str,
        email: str | None,
        uni_email: str | None,
        studiengang_name: str,
        anzahl_monate: int,
        anzahl_kurse: int,
        ects_gesamt: int,
        ziel_notenschnitt: float,
        ziel_enddatum: date,
        start_datum: date | None = None,
    ) -> tuple[int, int, int]:
        """
        Erstellt: Student + Studiengang + Einschreibung.
        Gibt (student_id, studiengang_id, einschreibung_id) zurück.
        """
        # 1) Student
        student = Student(
            name=student_name.strip(),
            matrikelnummer=matrikelnummer.strip(),
            email=email,
            uni_email=uni_email,
        )
        student_id = self._students.create(student)

        # 2) Studiengang
        sg = Studiengang(
            name=studiengang_name.strip(),
            anzahl_monate=int(anzahl_monate),
            anzahl_kurse=int(anzahl_kurse),
            ects_gesamt=int(ects_gesamt),  # bei dir heißt es im Model ggf. anders (ects_gesamt/ ziel_ects)
        )
        studiengang_id = self._studiengaenge.create(sg)

        # 3) Einschreibung (Ziele gehören hierhin!)
        e = Einschreibung(
            student_id=student_id,
            studiengang_id=studiengang_id,
            start_datum=start_datum or date.today(),
            ziel_enddatum=ziel_enddatum,
            ziel_notenschnitt=float(ziel_notenschnitt),
            status=StatusEinschreibung.AKTIV,
        )

        einschreibung_id = self._einschreibungen.create(e)

        return student_id, studiengang_id

    # ---------------------------------------------------------------------
    # Studenten
    # ---------------------------------------------------------------------

    def student_all(self) -> Iterable[Student]:
        """Liefert alle Studenten."""
        return self._students.all()

    def student_by_id(self, student_id: int) -> Optional[Student]:
        """Liefert einen Studenten per ID oder None."""
        return self._students.get_by_id(student_id)

    # ---------------------------------------------------------------------
    # Studiengang & Einschreibung
    # ---------------------------------------------------------------------

    def studiengaenge_by_student_id(self, student_id: int) -> List[Studiengang]:
        """
        Liefert alle Studiengänge, in die der Student eingeschrieben ist.
        (über Einschreibungen verknüpft)
        """
        einschreibungen = self._einschreibungen.list_by_student(student_id)
        ids = [e.studiengang_id for e in einschreibungen]
        result: List[Studiengang] = []
        for sg_id in ids:
            sg = self._studiengaenge.get_by_id(sg_id)
            if sg:
                result.append(sg)
        return result
    
    def selected_studiengang(self, student_id: int, studiengang_id: int) -> Optional[Studiengang]:
        """
        Liefert den ausgewählten Studiengang, falls der Student dort eingeschrieben ist.

        Warum:
        - UI/CLI dürfen beliebige IDs schicken -> Service schützt fachlich.
        - Gibt None zurück, wenn Auswahl ungültig ist (z.B. kein Zugriff / falsche ID).
        """
        # 1) Prüfen, ob Student in diesen Studiengang eingeschrieben ist
        einschreibungen = self.einschreibungen_fuer_student(student_id)
        if not any(e.studiengang_id == studiengang_id for e in einschreibungen):
            return None

        # 2) Studiengang laden
        return self.studiengang_by_id(studiengang_id)

    def studiengang_by_id(self, studiengang_id: int) -> Optional[Studiengang]:
        """Liefert Studiengang per ID"""
        return self._studiengaenge.get_by_id(studiengang_id)
    
    def studiengang_options_fuer_student(self, student_id: int) -> list[StudiengangOption]:
        """
        """
        einschreibungen = self.einschreibungen_fuer_student(student_id)
        if not einschreibungen:
            return []

        aktive = [e for e in einschreibungen if e.ist_aktiv]
        auswahl = aktive if aktive else einschreibungen

        opts: list[StudiengangOption] = []
        for e in auswahl:
            if e.studiengang_id is None:
                continue
            sg = self.studiengang_by_id(e.studiengang_id)
            label = sg.name if sg else f"Studiengang #{e.studiengang_id}"
            opts.append(
                StudiengangOption(
                    id=e.studiengang_id,
                    label=label,
                    ist_default=e.ist_aktiv,
                )
            )

        return opts

    def einschreibungen_fuer_student(self, student_id: int) -> List[Einschreibung]:
        """Alle Einschreibungen eines Studenten."""
        return self._einschreibungen.list_by_student(student_id)

    def aktive_einschreibung(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> Optional[Einschreibung]:
        """
        Liefert die aktive Einschreibung des Studenten.

        - Ohne studiengang_id: erste aktive Einschreibung (wie bisher).
        - Mit studiengang_id: aktive Einschreibung genau für diesen Studiengang.
        """
        einschreibungen = self._einschreibungen.list_by_student(student_id)

        if studiengang_id is not None:
            for e in einschreibungen:
                if e.studiengang_id == studiengang_id and e.ist_aktiv:
                    return e
            return None

        # Fallback: "irgendeine" aktive (alter Default)
        for e in einschreibungen:
            if e.ist_aktiv:
                return e

        return None

    # ---------------------------------------------------------------------
    # Kurse
    # ---------------------------------------------------------------------

    def kurs_by_id(self, kurs_id: int) -> Optional[Kurs]:
        """Liefert einen Kurs per ID, wenn nicht vorhanden -> None."""
        return self._kurse.get_by_id(kurs_id)
    
    def kurs_name_exists(self, name: str, studiengang_id: Optional[int] = None) -> bool:
        return self._kurse.exists_by_name(name, studiengang_id)

    def kurs_kuerzel_exists(self, kuerzel: str, studiengang_id: Optional[int] = None) -> bool:
        return self._kurse.exists_by_kuerzel(kuerzel, studiengang_id)

    def kurse_fuer_student(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> List[Kurs]:
        """
        📚 Liefert alle Kurse eines Studenten.
        - Ohne studiengang_id: alle Kurse aus allen Studiengängen
        - Mit studiengang_id: nur Kurse dieses Studiengangs

        Ableitung erfolgt über Bearbeitungen:
        Student → Bearbeitung → Kurs
        """
        kurse: dict[int, Kurs] = {}

        # 1) Alle (oder gefilterte) Bearbeitungen laden
        bearbeitungen = self.bearbeitungen_fuer_student(
            student_id=student_id,
            studiengang_id=studiengang_id,
        )

        # 2) Kurse aus den Bearbeitungen ableiten
        for b in bearbeitungen:
            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            # Safety: Studiengang filtern (falls Bearbeitung alt/inkonsistent)
            if studiengang_id is not None and kurs.studiengang_id != studiengang_id:
                continue

            # dict verhindert Duplikate automatisch
            kurse[kurs.id] = kurs

        # 3) Als Liste zurückgeben (optional sortiert)
        return sorted(kurse.values(), key=lambda k: (k.semester_nr or 0, k.name))


    
    # ---------------------------------------------------------------------
    # Bearbeitungen, Prüfungen
    # ---------------------------------------------------------------------

    def bearbeitungen_fuer_student(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> List[Bearbeitung]:
        """
        Liefert Bearbeitungen eines Studenten.
        - Ohne studiengang_id: alle Bearbeitungen
        - Mit studiengang_id: nur Bearbeitungen, deren Kurs zu diesem Studiengang gehört
        """
        bearbeitungen = list(self._bearb.list_by_student(student_id))

        if studiengang_id is None:
            return bearbeitungen

        result: List[Bearbeitung] = []
        for b in bearbeitungen:
            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue
            if kurs.studiengang_id != studiengang_id:
                continue
            result.append(b)

        return result
    
    def inaktive_bearbeitungen(self, student_id: int, studiengang_id: Optional[int] = None):
        """Liefert inaktive Bearbeitung mit kurs und label."""
        out = []
        for b in self.bearbeitungen_fuer_student(student_id, studiengang_id):
            if b.status != StatusBearbeitung.INAKTIV:
                continue
            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue
            label = f"{(kurs.kurs_kuerzel + ' – ') if kurs.kurs_kuerzel else ''}{kurs.name}"
            out.append((b, kurs, label))
        return out
    
    def aktive_bearbeitungen(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> List[Tuple[Bearbeitung, Kurs, str]]:
        """Aktive Bearbeitungen (noch nicht eingereicht) inkl. Kurs + Label für UI."""
        out: List[Tuple[Bearbeitung, Kurs, str]] = []

        for b in self.bearbeitungen_fuer_student(student_id, studiengang_id):
            if b.status != StatusBearbeitung.AKTIV:
                continue
            if b.abgabe_datum is not None:
                continue

            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            kuerzel = (kurs.kurs_kuerzel or "").strip()
            label = f"{(kuerzel + ' – ') if kuerzel else ''}{kurs.name}"

            out.append((b, kurs, label))

        return out

    def eingereichte_bearbeitungen(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> List[Tuple[Bearbeitung, Kurs, Optional[Pruefung], str]]:
        """
        Liefert eingereichte Bearbeitungen inkl. Kurs + optionaler Prüfung + Label für UI.
        """
        out: List[Tuple[Bearbeitung, Kurs, Optional[Pruefung], str]] = []

        for b in self.bearbeitungen_fuer_student(student_id, studiengang_id):
            if b.status != StatusBearbeitung.EINGEREICHT:
                continue

            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            pruef = self.pruefung_fuer_bearbeitung(b.id) if b.id else None

            abgabe_str = b.abgabe_datum.strftime("%d.%m.%Y") if b.abgabe_datum else "kein Datum"
            kuerzel = (kurs.kurs_kuerzel or "").strip()
            titel = f"{(kuerzel + ' – ') if kuerzel else ''}{kurs.name}"

            if pruef is None or pruef.note is None:
                status_txt = "noch keine Note"
            else:
                status_txt = f"bisherige Note: {pruef.note}"

            label = f"{titel} – Abgabe: {abgabe_str} – {status_txt}"

            out.append((b, kurs, pruef, label))

        return out

    def abgeschlossene_bearbeitungen(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> List[AbgeschlosseneBearbeitung]:
        """
        Wie bisher – optional auf studiengang_id gefiltert.
        """
        result: List[AbgeschlosseneBearbeitung] = []

        # Wenn studiengang_id gesetzt ist, nutzen wir die gefilterten Bearbeitungen
        if studiengang_id is not None:
            bearbeitungen = self.bearbeitungen_fuer_student(student_id, studiengang_id=studiengang_id)
        else:
            bearbeitungen = self.bearbeitungen_fuer_student(student_id)

        for b in bearbeitungen:
            if b.status != StatusBearbeitung.ABGESCHLOSSEN:
                continue

            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            # Safety: falls jemand Bearbeitungen liefert, die nicht passen
            if studiengang_id is not None and kurs.studiengang_id != studiengang_id:
                continue

            pruefung = self.pruefung_fuer_bearbeitung(b.id)
            result.append(AbgeschlosseneBearbeitung(
                bearbeitung=b,
                kurs=kurs,
                pruefung=pruefung,
            ))

        return result

    def bearbeitungszeit_in_tagen(self, b: Bearbeitung) -> Optional[int]:
        """
        Gibt die Bearbeitungszeit in Tagen zurück (start_datum → abgabe_datum).
        """
        start = b.start_datum
        ende = b.abgabe_datum

        if not start or not ende:
            return None

        tage = (ende - start).days
        if tage < 0:
            return None
        return tage

    # ---------------------------------------------------------------------
    # Prüfungen
    # ---------------------------------------------------------------------

    def pruefungen_fuer_student(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> List[Tuple[Bearbeitung, Kurs, Pruefung]]:
        """
        Liefert alle vorhandenen Prüfungen eines Studenten
        (optional gefiltert nach Studiengang).

        Rückgabe:
        - nur Bearbeitungen, für die tatsächlich eine Prüfung existiert
        - jede Prüfung wird genau einer Bearbeitung und einem Kurs zugeordnet
        """
        result: List[Tuple[Bearbeitung, Kurs, Pruefung]] = []

        # Bearbeitungen (ggf. studiengang-gefiltert)
        bearbeitungen = self.bearbeitungen_fuer_student(student_id, studiengang_id)

        for b in bearbeitungen:
            if b.id is None:
                continue

            pruefung = self.pruefung_fuer_bearbeitung(b.id)
            if not pruefung:
                continue  # wenn Bearbeitung keine Prüfung, dann übersrpingen

            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            result.append((b, kurs, pruefung))

        return result

    
    def pruefung_fuer_bearbeitung(self, bearbeitung_id: int) -> Optional[Pruefung]:
        """Prüfung zu einer Bearbeitung, falls angelegt."""
        return self._pruef.get_by_bearbeitung_id(bearbeitung_id)


    # =====================================================================
    # Actionbar Methoden
    # =====================================================================

    # ---------------------------------------------------------------------
    # 1) Kurs hinzufügen
    # ---------------------------------------------------------------------

    def kurs_hinzufuegen(
        self,
        *,
        student_id: int,
        studiengang_id: int,
        name: str,
        kurs_kuerzel: str,
        ects: int,
        tutor: Optional[str] = None,
        semester_nr: Optional[int] = None,
        pruefungsform: Optional[Pruefungsform] = None,
        plan_start: Optional[date] = None,
        plan_end: Optional[date] = None,
        start_datum: Optional[date] = None,
    ) -> int:
        """
        Legt Kurs mit Bearbeitung an und (optional) eine Prüfung an.
        Rückgabe: kurs_id
        """

        # 1) Kurs erstellen
        kurs = Kurs(
            id=None,
            name=name,
            kurs_kuerzel=kurs_kuerzel,
            ects=int(ects),
            tutor=tutor,
            semester_nr=semester_nr,
            studiengang_id=studiengang_id,
        )
        kurs_id = self._kurse.create(kurs)

        # 2) Bearbeitung anlegen
        status = StatusBearbeitung.INAKTIV
        if start_datum:
            status = StatusBearbeitung.AKTIV

        bearb = Bearbeitung(
            id=None,
            student_id=student_id,
            kurs_id=kurs_id,
            status=status,
            plan_start=plan_start,
            plan_end=plan_end,
            start_datum=start_datum,
            abgabe_datum=None,
        )
        bearb_id = self._bearb.create(bearb)

        # 3) Optional Prüfung anlegen (wenn Prüfungsform gewählt)
        if pruefungsform is not None:
            pruef = Pruefung(
                id=None,
                bearbeitung_id=bearb_id,
                pruefungsform=pruefungsform,
                note=None,
                versuch_nr=0,
                bestanden=None,
                letzter_versuch=False,
            )
            self._pruef.create(pruef)

        return kurs_id

    # ---------------------------------------------------------------------
    # 2) Kurs starten
    # ---------------------------------------------------------------------

    def bearbeitung_starten(self, *, bearbeitung_id: int, start_datum: date) -> None:
        """Startet eine Bearbeitung: setzt start_datum und Status IN_BEARBEITUNG."""
        b = self._bearb.get_by_id(bearbeitung_id)
        if not b:
            raise ValueError("Bearbeitung nicht gefunden.")

        # Wenn schon gestartet -> nichts tun und Hinweis anzeigen
        if b.start_datum is not None:
            raise ValueError("Bearbeitung wurde bereits gestartet.")

        b.start_datum = start_datum
        b.status = StatusBearbeitung.AKTIV
        self._bearb.update(b)

    # ---------------------------------------------------------------------
    # 3) Prüfung abgeben
    # ---------------------------------------------------------------------

    def pruefung_abgeben(
        self,
        *,
        student_id: int,
        kurs_id: int,
        abgabe_datum: date,
    ) -> None:
        """Setzt für die Bearbeitung das Abgabedatum und Status EINGEREICHT."""
        # 1) Bearbeitung finden über Repo-Methode 
        bearbeitungen = self._bearb.list_by_student(student_id)
        b = next((x for x in bearbeitungen if x.kurs_id == kurs_id), None)
        if not b:
            raise ValueError("Keine Bearbeitung zu diesem Kurs gefunden.")

        # 2) abgeben
        b.abgabe_datum = abgabe_datum
        b.status = StatusBearbeitung.EINGEREICHT
        self._bearb.update(b)

    # ---------------------------------------------------------------------
    # 4) Note eintragen
    # ---------------------------------------------------------------------

    def note_eintragen(
        self,
        *,
        student_id: int,
        kurs_id: int,
        note: float,
    ) -> Pruefung:
        """
        Trägt eine Note ein und setzt die Bearbeitung abhängig davon auf ABGESCHLOSSEN
        oder zurück (wenn nicht bestanden).
        """
        # 1) Bearbeitung finden
        bearbeitungen = self._bearb.list_by_student(student_id)
        b = next((x for x in bearbeitungen if x.kurs_id == kurs_id), None)
        if not b or b.id is None:
            raise ValueError("Bearbeitung nicht gefunden.")

        # 2) Prüfung holen oder eine neue anlegen
        p = self._pruef.get_by_bearbeitung_id(b.id)
        if not p:
            p = Pruefung(bearbeitung_id=b.id)
            self._pruef.create(p)

        # 3) Domänenlogik aus Prüfung-Model ausführen
        p.note_eintragen(note)

        # 4) Bearbeitungsstatus anpassen
        if p.bestanden:
            b.status = StatusBearbeitung.ABGESCHLOSSEN

        # 5) persistieren
        self._pruef.update(p)
        self._bearb.update(b)

        return p

    # ---------------------------------------------------------------------
    # 5) Studium abschließen
    # ---------------------------------------------------------------------
    def studium_abschliessen(
        self,
        *,
        student_id: int,
        studiengang_id: int,
        notenschnitt: float,
    ) -> bool:
        """
        Schließt das Studium ab, wenn die Einschreibung gültig ist.
        """

        # 1) Einschreibung laden
        e = self.aktive_einschreibung(student_id, studiengang_id)
        if not e:
            raise ValueError("Keine aktive Einschreibung für diesen Studiengang gefunden.")

        # 2) Sicherheitscheck
        if e.status == StatusEinschreibung.ABGESCHLOSSEN:
            raise ValueError("Studium ist bereits abgeschlossen.")

        # 3) Abschluss über Domänenmethode
        e.abschliessen(
            enddatum=date.today(),
            notenschnitt=notenschnitt,
        )

        # 4) Persistieren
        self._einschreibungen.update(e)

        return True

