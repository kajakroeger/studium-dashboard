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
from typing import Optional

from models.bearbeitung import Bearbeitung, StatusBearbeitung


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

    id: int
    bearbeitung: Bearbeitung
    pruefungsform: Pruefungsform
    note: Optional[float] = None
    versuch_nr: int = 0
    bestanden: Optional[bool] = None
    letzter_versuch: bool = False  # neu: markiert, ob kein weiterer Versuch erlaubt ist

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
