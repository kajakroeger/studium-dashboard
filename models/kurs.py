from dataclasses import dataclass
from typing import Optional

@dataclass
class Kurs:
    """
    🥦 ZUTAT / LEBENSMITTEL (DOMÄNENMODELL)
    - repräsentiert einen Kurs im Studium
    - kennt nur seine eigenen Eigenschaften, keine Auswertungen, keine Darstellung

    Technisch:
    - reine Datenträger mit minimaler, fachlich sinnvoller Logik
    - keine Datenbankzugriffe
    - keine UI-Logik
    - keine Aggregationen oder Berechnungen über mehrere Objekte
    - wird von Repositories geladen/gespeichert
    - wird von Services verarbeitet 
    """
    name: str = ""
    kurs_kuerzel: str = ""
    ects: int = 0
    semester: int = 0
    studiengang_id: int = 0   # nötig für Filter pro Studiengang

    tutor: Optional[str] = None
    id: Optional[int] = None

     

    def __str__(self) -> str:
        """Lesbare Standardrepräsentation, z.B. für Logs."""
        semester_info = f" (Semester {self.semester})" if self.semester is not None else ""
        return f"{self.kurs_kuerzel}: {self.name} [{self.ects} ECTS]{semester_info}"

    @property
    def display_label(self) -> str:
        """Kurze Label-Variante für Dropdowns/Listen.
        Beispiel: "Software Engineering - SE1" """
        if self.kurs_kuerzel:
            return f"{self.name} - {self.kurs_kuerzel}"
        return self.name

    @property
    def short_label(self) -> str:
        """Kompakter, z.B. nur Kürzel oder gekürzter Name."""
        if self.kurs_kuerzel:
            return self.kurs_kuerzel
        return self.name if len(self.name) <= 20 else self.name[:17] + "..."
