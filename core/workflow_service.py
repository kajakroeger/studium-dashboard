# core/workflow_service.py
from __future__ import annotations
from datetime import date
from typing import Optional

from models import Student, Studiengang
from models.bearbeitung import Bearbeitung, StatusBearbeitung
from models.einschreibung import Einschreibung, StatusEinschreibung
from db.repositories.studiengang_repository import StudiengangRepository
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
        studiengang_repo: StudiengangRepository,   # ⬅️ wichtig: wird injiziert
        ects_summe_bestanden_fn,
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo
        self._studiengaenge = studiengang_repo      # ⬅️ speichern
        self._ects_summe_bestanden_fn = ects_summe_bestanden_fn

    # ------- Hilfsfunktion: liefert eine Studiengang-ID ------------------------
    def _ensure_studiengang(
        self,
        *,
        studiengang_id: Optional[int],
        name: Optional[str],
        anzahl_monate: Optional[int],
        anzahl_kurse: Optional[int],
        ects_gesamt: Optional[int],
    ) -> int:
        if studiengang_id is not None:
            return studiengang_id
        if not name or anzahl_monate is None or anzahl_kurse is None or ects_gesamt is None:
            raise ValueError("Studiengangdaten unvollständig (Name/Monate/Kurse/ECTS).")

        existing = self._studiengaenge.get_by_name(name)
        if existing and existing.id is not None:
            return existing.id

        sg = Studiengang(
            name=name,
            anzahl_monate=int(anzahl_monate),
            anzahl_kurse=int(anzahl_kurse),
            ects_gesamt=int(ects_gesamt),
        )
        return self._studiengaenge.create(sg)

    # --------------------------- Onboarding-Use-Case ---------------------------
    def create_student(
        self,
        *,
        name: str,
        matrikelnummer: str,
        email: Optional[str],
        uni_email: Optional[str],
        ziel_notenschnitt: float,
        ziel_enddatum: date,
        # Studiengang: entweder vorhandene ID ...
        studiengang_id: Optional[int] = None,
        # ... oder Felder zum Neuanlegen
        studiengang_name: Optional[str] = None,
        studiengang_monate: Optional[int] = None,
        studiengang_kurse: Optional[int] = None,
        studiengang_ects: Optional[int] = None,
    ) -> int:
        # 1) Student anlegen
        student = Student(
            name=name,
            matrikelnummer=matrikelnummer,
            email=email,
            uni_email=uni_email,
        )
        student_id = self._students.create(student)

        # 2) Studiengang-ID besorgen/erstellen
        sg_id = self._ensure_studiengang(
            studiengang_id=studiengang_id,
            name=studiengang_name,
            anzahl_monate=studiengang_monate,
            anzahl_kurse=studiengang_kurse,
            ects_gesamt=studiengang_ects,
        )

        # 3) Einschreibung mit Zielen speichern
        eins = Einschreibung(
            student_id=student_id,
            start_datum=date.today(),
            ziel_enddatum=ziel_enddatum,
            ziel_notenschnitt=ziel_notenschnitt,
            status=StatusEinschreibung.AKTIV,
            studiengang_id=sg_id,   # falls du stattdessen studiengang_name speicherst: hier anpassen
        )
        self._einschreibungen.create(eins)
        return student_id
    

    # Kurs mit Bearbeitung und optionaler Prüfung anlegen
    def add_kurs_mit_bearbeitung_und_pruefung(
        self,
        *,
        student_id: int,
        name: str,
        kuerzel: str,
        ects: int,
        tutor: Optional[str] = None,
        pruefungsform: Optional[Pruefungsform] = None,
        plan_start: Optional[date] = None,
        plan_ende: Optional[date] = None,
        start_datum: Optional[date] = None,
    ) -> int:
        # --- Validierung & Normalisierung ---
        name_clean = name.strip()
        ku_clean = kuerzel.strip()
        if not name_clean or not ku_clean:
            raise ValueError("Name und Kurskürzel dürfen nicht leer sein.")
        if ects <= 0:
            raise ValueError("ECTS muss > 0 sein.")

        # Eindeutigkeit sicherstellen (fachlich vorab prüfen)
        if self._kurse.exists_by_name(name_clean):
            raise ValueError(f"Ein Kurs mit dem Namen '{name_clean}' existiert bereits.")
        if self._kurse.exists_by_kuerzel(ku_clean):
            raise ValueError(f"Ein Kurs mit dem Kürzel '{ku_clean}' existiert bereits.")

        # 1) Kurs anlegen
        kurs = Kurs(
            name=name_clean,
            kurs_kuerzel=ku_clean,
            ects=int(ects),
            tutor=(tutor.strip() or None) if tutor else None,
            semester=0,
        )
        kurs_id = self._kurse.create(kurs)

        # 2) Bearbeitung anlegen
        status = StatusBearbeitung.AKTIV if start_datum else StatusBearbeitung.INAKTIV
        bearb = Bearbeitung(
            kurs_id=kurs_id,
            student_id=student_id,
            start_datum=start_datum,
            plan_start=plan_start,
            plan_end=plan_ende,
            status=status,
        )
        bearbeitung_id = self._bearb.create(bearb)

        # 3) Optionale Prüfung
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

    def kurs_name_exists(self, name: str) -> bool:
        # Trim im Service ist ok, damit UI/Backend gleich denken
        return self.kurs_repo.exists_by_name((name or "").strip())

    def kurs_kuerzel_exists(self, kuerzel: str) -> bool:
        return self.kurs_repo.exists_by_kuerzel((kuerzel or "").strip())
