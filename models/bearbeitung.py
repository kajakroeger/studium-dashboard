"""
Datei: bearbeitung.py
Beschreibung:
Dieses Modul definiert das Datenmodell 'Bearbeitung', das die Bearbeitung an einem Kurs beschreibt.
Z. B. kann es sich um eine Hausarbeit, Projektarbeit oder Laborleistung handeln.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from enum import Enum


class StatusBearbeitung(Enum):
    """Definiert die möglichen Status einer Bearbeitung."""
    INAKTIV = "inaktiv"
    AKTIV = "aktiv"
    PRUEFUNG_EINGEREICHT = "Prüfung eingereicht"
    ABGESCHLOSSEN = "abgeschlossen"


@dataclass
class Bearbeitung:
    """Repräsentiert eine Bearbeitung (z. B. Projekt, Hausarbeit) zu einem Kurs."""

    id: int
    kurs_id: int
    student_id: int
    plan_start: date                        # Geplantes Datum für den Start der Bearbeitung
    plan_end: date                          # Geplantes Datum für die Abgabe der Bearbeitung
    start_datum: date                       # Datum, an dem die Bearbeitung begonnen wurde
    abgabe_datum: Optional[date] = None     # Datum, an dem die Bearbeitung abgegeben wurde
    status:  StatusBearbeitung = StatusBearbeitung.INAKTIV  # Status der Bearbeitung


    def bearbeitung_abgeben(self, abgabe_datum: date):
        """Setzt das Abgabedatum und ändert den Status auf 'abgeschlossen'."""
        self.abgabe_datum = abgabe_datum
        self.status = StatusBearbeitung.ABGESCHLOSSEN

    def ist_abgeschlossen(self) -> bool:
        """Gibt True zurück, wenn die Bearbeitung abgeschlossen ist (d. h. Abgabedatum vorhanden)."""
        return self.abgabe_datum is not None

    def bearbeitungszeit(self) -> Optional[int]:
        """
        Gibt die Bearbeitungszeit in Tagen zurück, falls Abgabedatum vorhanden.
        Ansonsten None.
        """
        if self.abgabe_datum:
            return (self.abgabe_datum - self.start_datum).days
        return None
    

