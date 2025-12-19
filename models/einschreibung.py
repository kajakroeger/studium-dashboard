

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Optional

class StatusEinschreibung(Enum):
    AKTIV = "aktiv"
    INAKTIV= "inaktiv"
    ABGESCHLOSSEN = "abgeschlossen"
    ABGEBROCHEN = "abgebrochen"

@dataclass
class Einschreibung:
    """
    🥦 ZUTAT / LEBENSMITTEL (DOMÄNENMODELL)
    - repräsentiert die Einschreibung eines Studenten in einen Studiengang 
    - kennt nur seine eigenen Eigenschaften, keine Auswertungen, keine Darstellung

    Technisch:
    - reine Datenträger mit minimaler, fachlich sinnvoller Logik
    - keine Datenbankzugriffe
    - keine UI-Logik
    - keine Aggregationen oder Berechnungen über mehrere Objekte
    - wird von Repositories geladen/gespeichert
    - wird von Services verarbeitet 
    """
    student_id: int
    start_datum: date
    ziel_enddatum: date
    ziel_notenschnitt: float
    
    status: StatusEinschreibung = StatusEinschreibung.AKTIV
    end_datum: Optional[date] = None 
    abschluss_note: Optional[float] = None
    abbruch_grund: Optional[str] = None
    studiengang_id: Optional[int] = None
    id: Optional[int] = None  # Primärschlüssel, wird von der DB gesetzt

    def abschliessen(self, enddatum: date, notenschnitt: float) -> None:
        self.end_datum = enddatum
        self.abschluss_note = notenschnitt
        self.status = StatusEinschreibung.ABGESCHLOSSEN

    def abbrechen(self, enddatum: date, grund: Optional[str] = None) -> None:
        self.end_datum = enddatum    
        self.abbruch_grund = grund
        self.status = StatusEinschreibung.ABGEBROCHEN

    def dauer_bis_ziel(self) -> timedelta:
        return self.ziel_enddatum - self.start_datum
    
    def dauer_tatsaechlich(self) -> Optional[timedelta]:
        if self.end_datum is None:
            return None
        return self.end_datum - self.start_datum


    @property
    def ist_aktiv(self) -> bool:
        """Liefert True, wenn die Einschreibung aktiv ist"""
        return self.status == StatusEinschreibung.AKTIV

    @property
    def ist_abgeschlossen(self) -> bool:
        """Liefert True, wenn der Studiengang abgeschlossen wurde."""
        return self.status == StatusEinschreibung.ABGESCHLOSSEN

    @property
    def ist_abgebrochen(self) -> bool:
        """Liefert True, wenn die Einschreibung abgebrochen wurde."""
        return self.status == StatusEinschreibung.ABGEBROCHEN
