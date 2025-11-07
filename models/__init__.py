"""
models/__init__.py
Dieses Paket enthält alle Datenmodelle (Domain-Objekte) für das Studium-Dashboard.
Hier werden alle Klassen gebündelt exportiert, um sie bequem importieren zu können.
"""

from .student import Student
from .kurs import Kurs
from .bearbeitung import Bearbeitung, StatusBearbeitung
from .pruefung import Pruefung, Pruefungsform
from .einschreibung import Einschreibung, StatusEinschreibung
from .studiengang import Studiengang

__all__ = [
    "Student", 
    "Kurs", 
    "Bearbeitung", 
    "StatusBearbeitung",
    "Pruefung", 
    "Pruefungsform", 
    "Einschreibung", 
    "StatusEinschreibung",
    "Studiengang",
]

