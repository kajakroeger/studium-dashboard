# core/progress_service.py
"""
OPTIMIERT:
- Keine _to_date() Helper mehr (Repository liefert garantiert date-Objekte)
- Keine defensiven getattr()-Checks mehr (Typen sind garantiert)
- Properties statt repetitiver Helper-Funktionen
- Viel kürzere, klarere Methoden
"""
from __future__ import annotations
from typing import List, Optional, Tuple
from datetime import date

from models import Bearbeitung, Pruefung
from models.bearbeitung import StatusBearbeitung


class ProgressService:
    """
    Verantwortlich für:
    - KPI-Berechnungen (ECTS, Notenschnitt, Bearbeitungszeit)
    - Aggregationen (alle Noten, Verlauf der Bearbeitungszeiten)
    - Read-Only Operationen (keine Statusänderungen)
    """

    def __init__(
        self,
        *,
        student_repo,
        bearbeitung_repo,
        kurs_repo,
        pruefung_repo,
        einschreibung_repo,
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo
        self._workflow = None  # wird später gesetzt

    def set_workflow(self, workflow) -> None:
        """Wird vom FortschrittService nachträglich aufgerufen."""
        self._workflow = workflow


    # ==================== Noten ====================

    def alle_bestandenen_noten(self, student_id: int) -> List[float]:
        """
        VEREINFACHT (von 50 → 15 Zeilen):
        Gibt alle Noten aus bestandenen Prüfungen zurück.
        """
        if not self._workflow:
            return []

        bearbeitungen = self._workflow.bearbeitungen_fuer_student(student_id)
        noten = []

        for b in bearbeitungen:
            pruefung = self._pruef.get_by_bearbeitung_id(b.id)
            
            # Typsicher: pruefung.bestanden ist garantiert bool oder None
            if pruefung and pruefung.bestanden and pruefung.note is not None:
                noten.append(float(pruefung.note))

        return noten

    def berechne_notenschnitt(self, student_id: int) -> Optional[float]:
        """Berechnet den Notenschnitt aller bestandenen Prüfungen."""
        noten = self.alle_bestandenen_noten(student_id)
        
        if not noten:
            return None
        
        return round(sum(noten) / len(noten), 2)

    def benoetigte_note_naechster_kurs(self, student_id: int) -> Optional[float]:
        """
        Berechnet die Note, die im nächsten Kurs nötig ist,
        um die Zielnote zu erreichen.
        
        Returns:
            - Note [1.0, 5.0] wenn erreichbar
            - 1.0 wenn bereits besser als Ziel
            - None wenn mit einem Kurs nicht mehr erreichbar
        """
        # Zielnote aus aktiver Einschreibung
        einschreibung = self._workflow.aktive_einschreibung(student_id)
        if not einschreibung or not einschreibung.ziel_notenschnitt:
            return None

        ziel = einschreibung.ziel_notenschnitt
        noten = self.alle_bestandenen_noten(student_id)
        
        if not noten:
            return None

        # Formel: (summe + required) / (n + 1) = ziel
        summe = sum(noten)
        n = len(noten)
        required = ziel * (n + 1) - summe

        if required <= 1.0:
            return 1.0  # Ziel bereits erreicht/übererfüllt
        if required > 5.0:
            return None  # Mit einem Kurs nicht mehr machbar
        
        return round(required, 2)
    



    # ==================== ECTS ====================

    def ects_summe_bestanden(self, student_id: int) -> int:
        """Summe der ECTS für bestandene Prüfungen."""
        bearbeitungen = self._bearb.list_by_student(student_id)
        total = 0

        for b in bearbeitungen:
            pruefung = self._pruef.get_by_bearbeitung_id(b.id)
            
            if pruefung and pruefung.bestanden:
                kurs = self._kurse.get_by_id(b.kurs_id)
                if kurs:
                    total += kurs.ects

        return total

    # ==================== Bearbeitungszeiten ====================

    

    # ==================== Ziele ====================

    def benoetigter_durchschnitt_restliche_kurse(
        self, student_id: int
    ) -> Optional[Tuple[float, int]]:
        """
        Berechnet den nötigen Durchschnitt in den restlichen Kursen,
        um die Zielnote zu erreichen.
        
        Returns:
            (required_avg, rest_kurse) oder None
        """
        # Zielnote holen
        einschreibung = self._workflow.aktive_einschreibung(student_id)
        if not einschreibung or not einschreibung.ziel_notenschnitt:
            return None

        ziel = einschreibung.ziel_notenschnitt

        # Bisherige Noten
        noten = self.alle_bestandenen_noten(student_id)
        summe_bisher = sum(noten)
        n_bisher = len(noten)

        # Studiengang
        studiengaenge = self._workflow.studiengaenge_by_student_id(student_id)
        if not studiengaenge:
            return None

        studiengang = studiengaenge[0]
        gesamt_kurse = studiengang.anzahl_kurse
        
        if not gesamt_kurse:
            return None

        # Restliche Kurse
        rest_kurse = gesamt_kurse - n_bisher
        if rest_kurse <= 0:
            return None

        # Formel: (summe_bisher + rest_kurse * x) / gesamt_kurse = ziel
        required_avg = (ziel * gesamt_kurse - summe_bisher) / rest_kurse

        if required_avg > 5.0:
            return None  # Nicht mehr erreichbar
        
        if required_avg < 1.0:
            required_avg = 1.0

        return (round(required_avg, 2), rest_kurse)
