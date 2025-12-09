# core/progress_service.py
"""
OPTIMIERT:
- Keine _to_date() Helper mehr (Repository liefert garantiert date-Objekte)
- Keine defensiven getattr()-Checks mehr (Typen sind garantiert)
- Properties statt repetitiver Helper-Funktionen
- Viel kürzere, klarere Methoden
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from datetime import date, timedelta

from core.dtos import NotenZielStatus, TempoStatus
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
    




    def berechne_notenziel_status(self, student_id: int) -> NotenZielStatus:
        """
        Berechnet den kompletten Status für Noten-Ziele.
        """
        aktueller_schnitt = self.berechne_notenschnitt(student_id)

        if not self._workflow:
            return self._empty_notenziel_status()

        einschreibung = self._workflow.aktive_einschreibung(student_id)
        ziel_note = einschreibung.ziel_notenschnitt if einschreibung else None

        noten = self.alle_bestandenen_noten(student_id)
        gesamt_noten = sum(noten)
        anzahl_noten = len(noten)

        studiengaenge = self._workflow.studiengaenge_by_student_id(student_id)
        studiengang = studiengaenge[0] if studiengaenge else None
        gesamt_kurse = studiengang.anzahl_kurse if studiengang else None

        rest_kurse: Optional[int] = None
        if gesamt_kurse is not None:
            rest_kurse = max(gesamt_kurse - anzahl_noten, 0)

        benoetigte_note_naechster_kurs: Optional[float] = None
        benoetigter_durchschnitt_rest: Optional[float] = None
        best_moeglicher_schnitt: Optional[float] = None
        ziel_erreicht = False

        naechster_besserer_schnitt: Optional[float] = None
        note_fuer_naechsten_besseren_schnitt: Optional[float] = None
        note_fuer_minimale_verbesserung: Optional[float] = None

        # --- Standard-Zielnoten-Logik ---
        if ziel_note is not None and anzahl_noten > 0:
            # Bester möglicher Schnitt, wenn du im nächsten Kurs 1,0 schreibst
            best_moeglicher_schnitt = (gesamt_noten + 1.0) / (anzahl_noten + 1)

            # Note, um direkt die Zielnote zu erreichen (falls realistisch)
            direkte_note = self._note_fuer_ziel_schnitt(
                gesamt_noten=gesamt_noten,
                anzahl_noten=anzahl_noten,
                ziel_schnitt=ziel_note,
            )
            benoetigte_note_naechster_kurs = direkte_note  # kann None sein

            # Durchschnitt, der in allen restlichen Kursen nötig wäre
            if gesamt_kurse is not None and rest_kurse and rest_kurse > 0:
                required_avg = (ziel_note * gesamt_kurse - gesamt_noten) / rest_kurse
                if required_avg <= 5.0:
                    if required_avg < 1.0:
                        required_avg = 1.0
                    benoetigter_durchschnitt_rest = round(required_avg, 2)

        # --- Ziel erreicht? ---
        if aktueller_schnitt is not None and ziel_note is not None:
            ziel_erreicht = aktueller_schnitt <= ziel_note

        # --- Minimale Note zur Verbesserung des aktuellen Schnitts ---
        if aktueller_schnitt is not None and anzahl_noten > 0:
            note_fuer_minimale_verbesserung = self._benoetigte_note_fuer_verbesserung(
                aktueller_schnitt=aktueller_schnitt
            )

        return NotenZielStatus(
            aktueller_schnitt=aktueller_schnitt,
            ziel_note=ziel_note,
            benoetigte_note_naechster_kurs=benoetigte_note_naechster_kurs,
            benoetigter_durchschnitt_rest=benoetigter_durchschnitt_rest,
            best_moeglicher_schnitt_naechster_kurs=best_moeglicher_schnitt,
            rest_kurse=rest_kurse,
            anzahl_noten=anzahl_noten,
            ziel_erreicht=ziel_erreicht,
            naechster_besserer_schnitt=naechster_besserer_schnitt,
            note_fuer_naechsten_besseren_schnitt=note_fuer_naechsten_besseren_schnitt,
            note_fuer_minimale_verbesserung=note_fuer_minimale_verbesserung,
        )

    
    def _note_fuer_ziel_schnitt(
        self,
        gesamt_noten: float,
        anzahl_noten: int,
        ziel_schnitt: float,
    ) -> Optional[float]:
        """
        Berechnet die benötigte Note im nächsten Kurs für einen gewünschten Durchschnitt.
        Ergebnis:
        - auf eine Nachkommastelle gerundet (0.1-Raster)
        - None, wenn außerhalb des zulässigen Notenbereichs [1.0, 5.0]
        """
        # Rohwert berechnen
        raw = ziel_schnitt * (anzahl_noten + 1) - gesamt_noten

        # Auf 1 Nachkommastelle runden (z. B. 1.234 -> 1.2)
        needed = round(raw * 10) / 10.0

        # Zulässiger Notenbereich
        if needed < 1.0 or needed > 5.0:
            return None

        return needed


    def _benoetigte_note_fuer_verbesserung(
        self,
        aktueller_schnitt: float,
    ) -> Optional[float]:
        """
        Berechnet die schlechteste Note (mit einer Nachkommastelle),
        die den aktuellen Schnitt noch VERBESSERT.
        """
        base = math.floor(aktueller_schnitt * 10) / 10.0

        if base < aktueller_schnitt:
            needed = base
        else:
            needed = base - 0.1

        if needed < 1.0:
            return None

        return round(needed, 1)