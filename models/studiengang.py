"""
Datei: studiengang.py
Beschreibung:
Definiert das Datenmodell 'Studiengang', das einen kompletten Studiengang beschreibt,
bestehend aus mehreren Semestern.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Studiengang:
    """
    🥦 ZUTAT / LEBENSMITTEL (DOMÄNENMODELL)
    - repräsentiert einen Studiengang 
    - kennt nur seine eigenen Eigenschaften, keine Auswertungen, keine Darstellung

    Technisch:
    - reine Datenträger mit minimaler, fachlich sinnvoller Logik
    - keine Datenbankzugriffe
    - keine UI-Logik
    - keine Aggregationen oder Berechnungen über mehrere Objekte
    - wird von Repositories geladen/gespeichert
    - wird von Services verarbeitet 
    """
    name: str
    anzahl_monate: int
    anzahl_kurse: int
    ects_gesamt: int
    semester_anzahl: int
    id: Optional[int] = None  # Primärschlüssel, wird von der DB gesetzt

    def __str__(self) -> str:
        """Gibt den Namen des Studiengangs aus."""
        return f"{self.name} ({self.ects_gesamt} ECTS, {self.semester_anzahl} Semester)"
    
    @property
    def ziel_ects(self) -> int:
        """Gibt die Gesamt-ECTS des Studiengangs zurück."""
        return int(self.ects_gesamt or 0)
    



