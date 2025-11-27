"""
core/progress_service.py
Aggregation/Lesen (KPI, ECTS, Notenschnitt, Gesamtübersicht).
"""

from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Iterable
from typing import Optional

from core.workflow_service import WorkflowService
from models import Bearbeitung, Pruefung
from db.repositories.student_repository import StudentRepository
from db.repositories.bearbeitung_repository import BearbeitungRepository
from db.repositories.kurs_repository import KursRepository
from db.repositories.pruefung_repository import PruefungRepository
from db.repositories.einschreibung_repository import EinschreibungRepository


class ProgressService:
    def __init__(
        self,
        *,
        student_repo: StudentRepository,
        bearbeitung_repo: BearbeitungRepository,
        kurs_repo: KursRepository,
        pruefung_repo: PruefungRepository,
        einschreibung_repo: EinschreibungRepository,
        # workflow,
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo

        # Workflow wird später gesetzt
        self._workflow = None

    def set_workflow(self, workflow) -> None:
        """Wird vom FortschrittService nachträglich aufgerufen"""
        self._workflow = workflow


    def alle_bestandenen_noten(self, student_id: int) -> list[float]:
        """
        Gibt eine Liste aller Noten aus bestandenen Prüfungen eines Studenten zurück.
        Falls keine bestandenen Prüfungen vorhanden sind, wird eine leere Liste zurückgegeben.
        """

        # Prüfen, ob der Workflow korrekt gesetzt ist
        if self._workflow is None or not hasattr(self._workflow, "bearbeitungen_fuer_student"):
            print("DEBUG: Workflow fehlt oder bietet bearbeitungen_fuer_student nicht an")
            return []

        # 1) Bearbeitungen holen
        bearbeitungen = list(self._workflow.bearbeitungen_fuer_student(student_id) or [])

        if not bearbeitungen:
            return []

        # 2) Prüfungsrepository holen
        pruef_repo = getattr(self._workflow, "_pruef", None)
        if pruef_repo is None or not hasattr(pruef_repo, "get_by_bearbeitung_id"):
            print("DEBUG: Prüfungsrepository fehlt oder hat get_by_bearbeitung_id nicht")
            return []

        get_pruefung = pruef_repo.get_by_bearbeitung_id

        # 3) Noten einsammeln
        noten: list[float] = []

        for b in bearbeitungen:
            b_id = getattr(b, "id", None)
            if not b_id:
                continue

            p = get_pruefung(int(b_id))
            if not p:
                continue

            note = getattr(p, "note", None)
            bestanden_raw = getattr(p, "bestanden", 0)

            # Nur bestandene Prüfungen berücksichtigen
            if note is None or not bool(bestanden_raw):
                continue

            try:
                noten.append(float(note))
            except (TypeError, ValueError):
                continue

        return noten
    


    def benoetigte_note_naechster_kurs(self, student_id: int) -> Optional[float]:
        """
        Berechnet die benötigte Note im nächsten Kurs, um die Zielnote zu erreichen.
        Gibt:
        - eine Note im Bereich [1.0, 5.0], falls mit einem Kurs sinnvoll beeinflussbar
        - 1.0, falls du bereits so gut liegst, dass jede 1.0 hilft und alles darunter nur "Luxus" wäre
        - None, falls:
            * keine Zielnote hinterlegt ist
            * keine bestandenen Noten vorhanden sind
            * mit EINEM Kurs rechnerisch nicht mehr auf den Ziel-Schnitt zu kommen ist
        """

        ziel = self.berechne_ziel_notenschnitt(student_id)
        if ziel is None:
            return None

        noten = self.alle_bestandenen_noten(student_id)
        if not noten:
            return None

        gesamt = sum(noten)
        n = len(noten)

        # Formel: (gesamt + required) / (n + 1) = ziel
        required = ziel * (n + 1) - gesamt

        # Debug-Ausgaben zum Prüfen (kannst du später entfernen)
        print(f"[DEBUG] benoetigte_note_naechster_kurs: ziel={ziel}, n={n}, sum={gesamt}, required_roh={required}")

        # Wenn required <= 1.0, dann reicht jede 1.0 im nächsten Kurs locker,
        # d.h. Ziel ist auf jeden Fall mit einem Kurs erreichbar.
        if required <= 1.0:
            return 1.0

        # Wenn required > 5.0, dann kann man mit EINEM Kurs nichts mehr retten
        if required > 5.0:
            return None

        # Ansonsten liegt required im Bereich (1.0, 5.0]
        return round(required, 2)
    


    def benoetigte_durchschnittsnote_restliche_kurse(
        self, student_id: int
    ) -> Optional[tuple[float, int]]:
        """
        Berechnet, welchen Durchschnitt du in den verbleibenden Kursen
        mindestens brauchst, um deine Zielnote zu erreichen.

        Rückgabe:
            (required_avg, rest_kurse) oder None, wenn:
            - keine Zielnote hinterlegt ist
            - kein Studiengang / keine anzahl_kurse vorhanden ist
            - keine restlichen Kurse übrig sind
            - es mit den restlichen Kursen rechnerisch nicht mehr erreichbar ist
        """

        # Zielnote holen (z. B. aus aktiver Einschreibung)
        ziel = self.berechne_ziel_notenschnitt(student_id)
        if ziel is None:
            return None

        # Bisherige Noten (nur bestandene Prüfungen)
        noten = self.alle_bestandenen_noten(student_id) or []
        gesamt_bisher = sum(noten)
        n_bisher = len(noten)

        # Studiengang + anzahl_kurse holen
        studiengaenge = self.studiengaenge_fuer_student(student_id) or []
        if not studiengaenge:
            return None

        sg = studiengaenge[0]
        gesamt_kurse = getattr(sg, "anzahl_kurse", None)
        if gesamt_kurse is None:
            return None

        # Restliche Kurse
        rest_kurse = gesamt_kurse - n_bisher
        if rest_kurse <= 0:
            # nichts mehr offen → Notenschnitt ist faktisch „eingefroren“
            return None

        # Formel:
        # (gesamt_bisher + rest_kurse * required_avg) / gesamt_kurse = ziel
        required_avg = (ziel * gesamt_kurse - gesamt_bisher) / rest_kurse

        print(
            f"[DEBUG] ziel={ziel}, gesamt_kurse={gesamt_kurse}, n_bisher={n_bisher}, "
            f"sum={gesamt_bisher}, rest_kurse={rest_kurse}, required_avg_roh={required_avg}"
        )

        # Wenn man im Schnitt bessere Noten als 1.0 bräuchte → unrealistisch / nicht erreichbar
        if required_avg > 5.0:
            return None

        # Theoretisch kann required_avg < 1.0 sein, dann bist du eigentlich „über Plan“.
        # Für die Anzeige runden wir nach unten auf 1.0 (bessere Note gibt es nicht).
        if required_avg < 1.0:
            required_avg = 1.0

        return (round(required_avg, 2), rest_kurse)
    


    def berechne_notenschnitt(self, student_id: int) -> Optional[float]:
        """
        Berechnet den Notenschnitt aller bestandenen Prüfungen
        eines Studenten. Gibt None zurück, wenn es keine
        bestandenen Prüfungen gibt.
        """

        if self._workflow is None or not hasattr(self._workflow, "bearbeitungen_fuer_student"):
            print("DEBUG: Abbruch, weil _workflow fehlt oder keine bearbeitungen_fuer_student-Methode hat")
            return None

        # Sicherstellen, dass der Workflow gesetz wurde
        if self._workflow is None or not hasattr(self._workflow, "bearbeitungen_fuer_student"):
            return None

        # 1) Bearbeitungen über den Workflow holen
        #    -> hier liegt deine Methode bearbeitungen_fuer_student
        if not hasattr(self._workflow, "bearbeitungen_fuer_student"):
            # Falls der Workflow falsch oder nicht gesetzt ist
            return None

        # list() macht aus einem evtl. Iterator eine Liste
        bearbeitungen = list(self._workflow.bearbeitungen_fuer_student(student_id) or [])

        if not bearbeitungen:
            # Keine Bearbeitungen → kein Notenschnitt
            return None

        # 2) Prüfungs-Repository über den Workflow holen
        pruef_repo = getattr(self._workflow, "_pruef", None)
        if pruef_repo is None or not hasattr(pruef_repo, "get_by_bearbeitung_id"):
            return None

        get_pruefung = pruef_repo.get_by_bearbeitung_id

        # 3) Noten einsammeln (nur bestandene Prüfungen)
        noten: list[float] = []

        for b in bearbeitungen:
            b_id = getattr(b, "id", None)
            if not b_id:
                continue

            # Prüfung zu dieser Bearbeitung holen
            p = get_pruefung(int(b_id))
            if not p:
                continue

            note = getattr(p, "note", None)
            bestanden_raw = getattr(p, "bestanden", 0)  # 0/1, False/True oder None

            # Nur bestandene Prüfungen mit Note berücksichtigen
            if note is None or not bool(bestanden_raw):
                continue

            try:
                noten.append(float(note))
            except (TypeError, ValueError):
                # Falls note kein Zahlentyp ist → überspringen
                continue

        # 4) Durchschnitt berechnen
        if not noten:
            return None

        return round(sum(noten) / len(noten), 2)

    

    def ects_summe_bestanden(self, student_id: int) -> int:
        """Summe der ECTS für bestandene Prüfungen."""
        total = 0
        for b in self._bearb.einschreibungen_fuer_student(student_id):
            p = self._pruefung_fuer_bearbeitung(b.id)
            if p and getattr(p, "bestanden", False):
                kurs = self._kurse.get_by_id(b.kurs_id)
                total += getattr(kurs, "ects", 0)
        return total



    # Hilfsfunktion wie bisher
    def _pruefung_fuer_bearbeitung(self, bearbeitung_id: int) -> Optional[Pruefung]:
        return self._pruef.get_by_bearbeitung_id(bearbeitung_id)
    


    def _to_date(self, value) -> Optional[date]:
        """Hilfsfunktion: str/datetime/date -> date."""
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    def bearbeitungsdauer_in_tagen(self, b):
        """Gibt Bearbeitungsdauer einer Bearbeitung in Tagen zurück."""
        start = self._to_date(getattr(b, "start_datum", None))
        ende = self._to_date(getattr(b, "abgabe_datum", None))

        if not start or not ende:
            return None
        
        days = (ende - start).days
        return days if days >= 0 else None


    def verlauf_bearbeitungszeiten(self, student_id: int):
        """Liefert eine Liste der durchschnittlichen Bearbeitungszeiten nach jedem Abschluss."""
        if self._workflow is None:
            return []

        bearbeitungen = list(self._workflow.bearbeitungen_fuer_student(student_id) or [])

        # nur abgeschlossene + sortiert nach Abgabe
        fertige = [
            b for b in bearbeitungen
            if str(getattr(b.status, "value", b.status)).lower() == "abgeschlossen"
            and self._to_date(b.abgabe_datum)
        ]
        fertige.sort(key=lambda b: self._to_date(b.abgabe_datum))

        Verlauf = []
        summen = 0
        count = 0

        for b in fertige:
            tage = self.bearbeitungsdauer_in_tagen(b)
            if tage is None:
                continue
            
            summen += tage
            count += 1
            Verlauf.append(round(summen / count, 1))

        return Verlauf
    


    def berechne_bearbeitungszeit(self, student_id: int) -> Optional[float]:
        """
        Durchschnittliche Bearbeitungszeit pro 5 ECTS.

        Nutzt:
        - nur Bearbeitungen mit Status 'abgeschlossen'
        - nur Bearbeitungen mit start_datum UND abgabe_datum
        - ECTS aus dem Kurs, um auf 5 ECTS zu normieren
        """

        # Wir brauchen den Workflow, um bearbeitungen_fuer_student zu bekommen
        if self._workflow is None or not hasattr(self._workflow, "bearbeitungen_fuer_student"):
            return None

        bearbeitungen: List = list(self._workflow.bearbeitungen_fuer_student(student_id) or [])

        total_weighted_days = 0.0
        count = 0

        for b in bearbeitungen:
            # Status robust als Enum/Text auslesen
            raw_status = getattr(b, "status", "")
            status_text = getattr(raw_status, "value", raw_status)
            status_text = str(status_text).strip().lower()

            if status_text != "abgeschlossen":
                continue

            tage = self.bearbeitungsdauer_in_tagen(b)
            if tage is None:
                continue

            # Kurs + ECTS holen
            kurs = None
            if hasattr(self._kurse, "get_by_id"):
                kurs = self._kurse.get_by_id(b.kurs_id)
            elif hasattr(self._kurse, "get"):
                kurs = self._kurse.get(b.kurs_id)

            if not kurs:
                continue

            ects = getattr(kurs, "ects", 0) or 0
            if ects <= 0:
                continue

            # Auf 5 ECTS normieren
            weighted = tage * (5.0 / float(ects))

            total_weighted_days += weighted
            count += 1

        if count == 0:
            return None

        return round(total_weighted_days / count, 1)