"""
Datei: semester.py
Beschreibung:
Definiert das Modell 'Semester', das eine Sammlung von Kursen innerhalb eines Studiengangs darstellt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    # Nur für Typprüfung – wird nicht zur Laufzeit importiert:
    from .kurs import Kurs


@dataclass
class Semester:
    """Repräsentiert ein Semester mit mehreren Kursen."""

    nummer: int
    kurse: List[Kurs] = field(default_factory=list)

    def kurs_hinzufuegen(self, kurs: Kurs) -> None:
        """Fügt dem Semester einen Kurs hinzu und setzt den Rückverweis."""
        self.kurse.append(kurs)
        kurs.semester = self  
        print(f"📘 Kurs '{kurs.name}' wurde Semester {self.nummer} hinzugefügt.")

    def __str__(self) -> str:
        return f"Semester {self.nummer} ({len(self.kurse)} Kurse)"
