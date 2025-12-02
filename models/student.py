"""
Definiert das Datenmodell 'Student', das einen Studierenden repräsentiert.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from models.einschreibung import Einschreibung


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

    name: str
    matrikelnummer: str
    email: Optional[str] = None
    uni_email: Optional[str] = None
    id: Optional[int] = None  # Primärschlüssel, wird von der DB gesetzt
    
    einschreibungen: List["Einschreibung"] = field(default_factory=list)



    def __str__(self) -> str:
        """Liefert eine einfache Textrepräsentation für Debugging und Logs."""
        return f"{self.name} ({self.matrikelnummer})"

    