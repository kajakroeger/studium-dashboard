"""
Datei: studiengang.py
Beschreibung:
Definiert das Datenmodell 'Studiengang', das einen kompletten Studiengang beschreibt,
bestehend aus mehreren Semestern.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .semester import Semester


@dataclass
class Studiengang:
    """Repräsentiert einen kompletten Studiengang (z. B. Informatik B.Sc.)."""

    name: str
    anzahl_monate: int
    anzahl_kurse: int
    ects_gesamt: int
    semester: List[Semester] = field(default_factory=list)
    id: Optional[int] = None  # Primärschlüssel, wird von der DB gesetzt

    def __str__(self) -> str:
        """Gibt den Namen des Studiengangs aus."""
        return f"{self.name} ({self.ects_gesamt} ECTS, {len(self.semester)} Semester)"
    
    @property
    def ziel_ects(self) -> int:
        """Gibt die Gesamt-ECTS des Studiengangs zurück."""
        return int(self.ects_gesamt or 0)
    



