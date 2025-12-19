
# db/models/__init__.py
"""
🥦📋 ZUTATENKATALOG (DOMÄNENMODELLE)

- bündelt alle Domänenobjekte des Systems
- beschreibt *was existiert* im fachlichen Sinne:
  Student, Kurs, Bearbeitung, Prüfung, Einschreibung, Studiengang

In der Analogie:
- Models sind die Zutaten selbst:
  - sie haben Eigenschaften (Name, ECTS, Status, Datum)
  - sie enthalten nur minimale, fachlich sinnvolle Logik
  - sie wissen NICHT:
    - woher sie kommen (DB)
    - wer sie kombiniert (Services)
    - wie sie dargestellt werden (UI)

Technisch:
- reine Python-Datenklassen + Enums
- keine Datenbankzugriffe
- keine Service- oder UI-Abhängigkeiten
- werden von Repositories geladen/gespeichert
- werden von Services verarbeitet
- from models import * → importiert den ganzen fachlichen Bestand des Systems
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

