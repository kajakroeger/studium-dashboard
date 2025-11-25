"""
Datei: kurs.py
Beschreibung:
Dieses Modul definiert das Datenmodell 'Kurs', das einen Kurs im Studium beschreibt.
Ein Kurs gehört zu genau einem Semester.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # NUR für Typprüfung, nicht zur Laufzeit importieren
    from .semester import Semester


@dataclass
class Kurs:
    """Repräsentiert einen Kurs oder ein Modul des Studiengangs."""

    name: str
    kurs_kuerzel: str
    ects: int
    tutor: str
    semester: Optional[int] = None  # Rückverweis auf das zugehörige Semester
    id: Optional[int] = None  # Primärschlüssel, wird von der DB gesetzt

    def __str__(self) -> str:
        semester_info = f" (Semester {self.semester.nummer})" if self.semester else ""
        return f"{self.kurs_kuerzel}: {self.name} [{self.ects} ECTS]{semester_info}"
