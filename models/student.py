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
    👨‍💻 USER/GAST (DOMÄNENMODELL)
    - repräsentiert einen Studierenden, der die UI bedient und sein Studium absolviert 
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
    matrikelnummer: str
    email: Optional[str] = None
    uni_email: Optional[str] = None
    id: Optional[int] = None  # Primärschlüssel, wird von der DB gesetzt
    
    einschreibungen: List["Einschreibung"] = field(default_factory=list)



    def __str__(self) -> str:
        """Liefert eine einfache Textrepräsentation für Debugging und Logs."""
        return f"{self.name} ({self.matrikelnummer})"

    