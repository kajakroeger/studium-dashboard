from dataclasses import dataclass
from typing import Optional


@dataclass
class Kurs:
    name: str
    kurs_kuerzel: str
    ects: int
    tutor: str
    semester: Optional[int] = None  
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
            return f"{self.name} - {self.kurs_kuerzel} "
        return self.name

    @property
    def short_label(self) -> str:
        """Kompakter, z.B. nur Kürzel oder gekürzter Name."""
        if self.kurs_kuerzel:
            return self.kurs_kuerzel
        return self.name if len(self.name) <= 20 else self.name[:17] + "..."
