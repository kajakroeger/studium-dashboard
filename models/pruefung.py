"""
Datei: pruefung.py
Beschreibung:
Diese Klasse modelliert eine Prüfung zu einer Bearbeitung.
Die Methode note_eintragen() erlaubt das Eintragen einer neuen Note,
prüft automatisch, ob bestanden wurde, und handhabt bis zu 3 Versuche.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

from models.bearbeitung import Bearbeitung, StatusBearbeitung

# Typing-Hinweis zur Vermeidung von zirkulären Importen
if TYPE_CHECKING:
    from models.bearbeitung import Bearbeitung


class Pruefungsform(Enum):
    """Mögliche Prüfungsformen."""
    KLAUSUR = "Klausur"
    PRAESENTATION = "Präsentation"
    WORKBOOK = "Workbook"
    FALLSTUDIE = "Fallstudie"
    PROJEKTBERICHT = "Projektbericht"
    SEMINARARBEIT = "Seminararbeit"
    PORTFOLIO = "Portfolio"
    ABSCHLUSSPRUEFUNG = "Abschlussprüfung"


@dataclass
class Pruefung:
    """Repräsentiert eine Prüfung (z. B. Klausur oder Projektprüfung) zu einer Bearbeitung."""
    pruefungsform: Pruefungsform
    bearbeitung_id: int = 0
    versuch_nr: int = 0
    note: Optional[float] = None
    bestanden: Optional[bool] = None
    letzter_versuch: bool = False  # markiert, ob kein weiterer Versuch erlaubt ist
    id: Optional[int] = None


    def __post_init__(self):
        """Validierung nach der Instanziierung."""
        if self.note is not None:
            if not (1.0 <= self.note <= 5.0):
                raise ValueError(f"Note muss zwischen 1.0 und 5.0 liegen, nicht {self.note}")
        
        if self.versuch_nr < 0:
            raise ValueError("Versuch-Nr kann nicht negativ sein")
        
        if self.versuch_nr > 3:
            raise ValueError("Maximal 3 Versuche erlaubt")

    def note_eintragen(self, note: float) -> None:
        """
        Trägt eine Note ein, erhöht den Versuchszähler und prüft, ob bestanden wurde.
        - Bei Note <= 4.0 → bestanden = True, Bearbeitung abgeschlossen
        - Bei Note > 4.0 → bestanden = False, Versuch wird erhöht
        - Nach 3 Fehlversuchen → letzter_versuch = True
        """
        # Sicherheitsprüfung: Keine weiteren Versuche, wenn bereits letzter Versuch
        if self.letzter_versuch:
            raise ValueError("Es sind keine weiteren Versuche mehr erlaubt (bereits letzter Versuch erreicht).")

        # Versuchszähler erhöhen
        self.versuch_nr += 1
        self.note = note

        # Prüfungsergebnis setzen
        if note <= 4.0:
            self.bestanden = True
            self.bearbeitung.status = StatusBearbeitung.ABGESCHLOSSEN
            print(f"✅ Prüfung bestanden im {self.versuch_nr}. Versuch (Note: {note}).")
        else:
            self.bestanden = False
            print(f"❌ Prüfung NICHT bestanden im {self.versuch_nr}. Versuch (Note: {note}).")

            # Wenn 3 Versuche nicht bestanden → letzter Versuch erreicht
            if self.versuch_nr >= 3:
                self.letzter_versuch = True
                print("⚠️  Letzter Versuch erreicht — keine weiteren Prüfungen mehr möglich.")

    def __str__(self) -> str:
        """Lesbare Textdarstellung."""
        return (
            f"Prüfung ({self.pruefungsform.value}) | Versuch: {self.versuch_nr} | "
            f"Note: {self.note} | Bestanden: {self.bestanden} | Letzter Versuch: {self.letzter_versuch}"
        )
