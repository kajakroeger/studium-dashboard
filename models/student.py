"""
Datei: models/student.py
Beschreibung:
Definiert das Datenmodell 'Student', das einen Studierenden repräsentiert.
Ein Student kann sich in Studiengänge einschreiben.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
from datetime import date

# TYPE_CHECKING vermeidet zirkulare Laufzeitimporte
if TYPE_CHECKING:
    from .einschreibung import Einschreibung
    from .studiengang import Studiengang


@dataclass
class Student:
    """
    Repräsentiert einen Studierenden.
    Attribute:
        id: Eindeutige ID in der Datenbank
        name: Vollständiger Name des Studierenden
        matrikelnummer: Eindeutige Matrikelnummer
        email: Private E-Mail-Adresse (optional)
        uni_email: Universitätsadresse (optional)
    """

    id: int
    name: str
    matrikelnummer: str
    email: Optional[str] = None
    uni_email: Optional[str] = None

    # Eine Liste aller Einschreibungen dieses Studierenden
    einschreibungen: List["Einschreibung"] = field(default_factory=list)

    def __str__(self) -> str:
        """Liefert eine einfache Textrepräsentation für Debugging und Logs."""
        return f"{self.name} ({self.matrikelnummer})"

    def einschreiben_studiengang(
        self,
        studiengang: "Studiengang",
        start_datum: date,
        ziel_enddatum: date,
        ziel_notenschnitt: float,
    ) -> "Einschreibung":
        """
        Erstellt eine neue Einschreibung für den Studenten.
        Der Import wird innerhalb der Methode gemacht, um Importzyklen zu vermeiden.
        """
        from .einschreibung import Einschreibung  # lokaler Import

        einschreibung = Einschreibung(
            student=self,
            studiengang=studiengang,
            start_datum=start_datum,
            ziel_enddatum=ziel_enddatum,
            ziel_notenschnitt=ziel_notenschnitt,
        )
        self.einschreibungen.append(einschreibung)
        return einschreibung
