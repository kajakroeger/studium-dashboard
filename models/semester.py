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
    """
    🥦 ZUTAT / LEBENSMITTEL (DOMÄNENMODELL)
    - repräsentiert ein Semester mit mehreren Kursen eines Studiums
    - kennt nur seine eigenen Eigenschaften, keine Auswertungen, keine Darstellung

    Technisch:
    - reine Datenträger mit minimaler, fachlich sinnvoller Logik
    - keine Datenbankzugriffe
    - keine UI-Logik
    - keine Aggregationen oder Berechnungen über mehrere Objekte
    - wird von Repositories geladen/gespeichert
    - wird von Services verarbeitet 
    """
    nummer: int
    kurse: List[Kurs] = field(default_factory=list)

    def kurs_hinzufuegen(self, kurs: "Kurs") -> None:
        """Fügt dem Semester einen Kurs hinzu und setzt die Semester-Nummer im Kurs."""
        self.kurse.append(kurs)
        kurs.semester_nr = self.nummer  

    def __str__(self) -> str:
        return f"Semester {self.nummer} ({len(self.kurse)} Kurse)"
