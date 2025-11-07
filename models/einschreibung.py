"""
Datei: einschreibung.py
Beschreibung:
Definiert die Domänenobjekte für die Einschreibung eines Studenten in einen Studiengang.
Enthält:
- StatusEinschreibung (Enum)
- Einschreibung (mit Start-/Zieldaten, Ziel-Notenschnitt und Status)
- Fachliche Methoden zum Abschließen/Abbrechen und zur Dauerberechnung
"""

# ganz oben:
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # NUR für Typprüfung, nicht zur Laufzeit importieren
    from .student import Student
    from .studiengang import Studiengang


class StatusEinschreibung(Enum):
    AKTIV = "aktiv"
    ABGESCHLOSSEN = "abgeschlossen"
    ABGEBROCHEN = "abgebrochen"


@dataclass
class Einschreibung:
    student_id: int
    start_datum: date
    ziel_enddatum: date
    ziel_notenschnitt: float
    status: StatusEinschreibung = StatusEinschreibung.AKTIV
    studiengang_id: Optional[int] = None
    id: Optional[int] = None  # Primärschlüssel, wird von der DB gesetzt

    enddatum_tatsaechlich: Optional[date] = None
    notenschnitt_tatsaechlich: Optional[float] = None
    abbruch_grund: Optional[str] = None

    def abschliessen(self, enddatum: date, notenschnitt: float) -> None:
        self.enddatum_tatsaechlich = enddatum
        self.notenschnitt_tatsaechlich = notenschnitt
        self.status = StatusEinschreibung.ABGESCHLOSSEN

    def abbrechen(self, grund: Optional[str] = None, enddatum: Optional[date] = None) -> None:
        self.abbruch_grund = grund
        self.enddatum_tatsaechlich = enddatum
        self.status = StatusEinschreibung.ABGEBROCHEN

    def dauer_bis_ziel(self) -> timedelta:
        return self.ziel_enddatum - self.start_datum
    
    def dauer_tatsaechlich(self) -> Optional[timedelta]:
        if self.enddatum_tatsaechlich is None:
            return None
        return self.enddatum_tatsaechlich - self.start_datum

