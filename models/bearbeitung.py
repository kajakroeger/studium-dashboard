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
    EINGEREICHT = "Prüfung eingereicht"
    ABGESCHLOSSEN = "abgeschlossen"


@dataclass
class Bearbeitung:
    """Repräsentiert eine Bearbeitung (z. B. Projekt, Hausarbeit) zu einem Kurs."""

    student_id: int
    kurs_id: int
    plan_start: Optional[date] = None                       # Geplantes Datum für den Start der Bearbeitung
    plan_end: Optional[date] = None                         # Geplantes Datum für die Abgabe der Bearbeitung
    start_datum: Optional[date] = None   
    abgabe_datum: Optional[date] = None                     # Datum, an dem die Bearbeitung abgegeben wurde
    status:  StatusBearbeitung = StatusBearbeitung.INAKTIV  # Status der Bearbeitung
    id: Optional[int] = None                # Primärschlüssel, wird von der DB gesetzt


    def kann_eingereicht_werden(self) -> bool:
        """Prüft, ob diese Bearbeitung eingereicht werden kann."""
        return self.status == StatusBearbeitung.AKTIV and self.abgabe_datum is None

    def bearbeitung_abgeben(self, abgabe_datum: date):
        """Reicht die Bearbeitung ein (setzt Datum und ändert Status)."""
        if not self.kann_eingereicht_werden():
            raise ValueError(
                f"Bearbeitung kann nicht eingereicht werden (Status: {self.status.value}, "
                f"Abgabe: {self.abgabe_datum})"
            )
        
        self.abgabe_datum = abgabe_datum
        self.status = StatusBearbeitung.eingereicht

    def ist_abgeschlossen(self) -> bool:
        """Gibt True zurück, wenn die Bearbeitung abgeschlossen ist (d. h. Abgabedatum vorhanden)."""
        return self.abgabe_datum is not None

    def bearbeitungszeit(self) -> Optional[int]:
        """Gibt die Bearbeitungszeit in Tagen zurück,falls Start- und Abgabedatum vorhanden sind."""
        if self.start_datum is None or self.abgabe_datum is None:
            return None
        return (self.abgabe_datum - self.start_datum).days
    

