# core/dtos.py
"""
❄️📦 KÜHLSCHRANK-BOXEN
- enthalten die vom Koch (ProgressSerivce) vorbereiteten Gerichte, die vom 'Anrichter' (ViewModelBuilder) angerichtet werden können.

Technisch:
- reine Datenträger (keine Geschäftslogik).
- dient als stabile Schnittstelle zwischen Service-Layer und Präsentationsschicht (ViewModelBuilder).
- DTOs sind UI-nahe Sichten, keine Domänenobjekte (Models, wie Kurs oder Bearbeitung)
- vorverarbeitete Sichten, die Daten für Dashbaord-Kacheln aggregiert, filtert, sortiert
"""


from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from models.bearbeitung import Bearbeitung
from models.kurs import Kurs
from models.pruefung import Pruefung

@dataclass(frozen=True)
class StudiengangOption:
    id: int
    label: str
    ist_default: bool = False

@dataclass
class AbgeschlosseneBearbeitung:
    """
    Hilfsobjekt für Analysen:
    kombinierte Sicht auf Bearbeitung + Kurs + Prüfung.
    """
    bearbeitung: Bearbeitung
    kurs: Kurs
    pruefung: Optional[Pruefung]

# =====================================================================
# 1) Studienziele
# =====================================================================

@dataclass
class StudienzieleDaten:
    """Vorbereitete Daten für die Studienziele."""
    ziel_notenschnitt: Optional[float]
    ziel_enddatum: Optional[date]
    start_datum: Optional[date]

# =====================================================================
# 2) Studienziele Status
# =====================================================================

@dataclass
class StudienzieleStatusDaten:
    """Vorbereitete Daten für den Status der Studienziele."""
    aktueller_schnitt: Optional[float] = None
    ziel_note: Optional[float] = None
    benoetigte_note_naechster_kurs: Optional[float] = None
    benoetigter_durchschnitt_rest: Optional[float] = None
    best_moeglicher_schnitt_naechster_kurs: Optional[float] = None
    rest_kurse: Optional[int] = None
    anzahl_noten: int = 0

    ziel_erreicht: bool = False
    naechster_besserer_schnitt: Optional[float] = None
    note_fuer_minimale_verbesserung: Optional[float] = None

    ist_tage_pro_5ects: Optional[float] = None
    ziel_tage_pro_5ects: float = 30.0           # Default für die durchschnittliche Bearbeitungszeit
    tempo_abweichung: Optional[float] = None
    prognose_enddatum: Optional[date] = None
    diff_tage_zum_ziel: Optional[int] = None


# =====================================================================
# 3) Status-Übersicht
# =====================================================================

@dataclass
class StatusUebersichtDaten:
    """Vorbereitete Daten für die Status-Übersicht."""
    ects_bestanden: float = 0.0
    ects_gesamt: Optional[float] = None
    ects_offen: Optional[float] = None
    ects_prozent: Optional[float] = None

    notenschnitt: Optional[float] = None
    beste_note: Optional[float] = None
    anzahl_noten: Optional[int] = None

    bearbeitungszeit_pro_5ects: Optional[float] = None
    durchschnitt_tage: Optional[float] = None


# =====================================================================
# 4) Burndown Chart
# =====================================================================

@dataclass
class BurndownDaten:
    """Vorbereitete Daten für Burndown Chart."""
    ziel_ects: float
    start_datum: date
    ziel_enddatum: Optional[date]

    abgeschlossene_kurse: List[Tuple[date, str, int]] = field(default_factory=list) # (abschluss_datum, kursname, ects)


# =====================================================================
# 5) Notenverlauf
# =====================================================================

@dataclass
class NotenverlaufDaten:
    """Vorbereitete Daten für Notenverlauf."""
    aktueller_schnitt: Optional[float] 
    beste_note: Optional[float]

    kursnamen: List[str] = field(default_factory=list)
    noten: List[float] = field(default_factory=list)
    pruefungsformen: List[str] = field(default_factory=list)
    durchschnittsverlauf: List[float] = field(default_factory=list)

# =====================================================================
# 6) Bearbeitungsverlauf
# =====================================================================

@dataclass
class BearbeitungsverlaufRohEintrag:
    """Rohdaten eines Eintrags im Bearbeitungsverlauf."""
    kurs_name: str
    kurs_kuerzel: Optional[str]
    start_datum: Optional[date]
    abgabe_datum: Optional[date]
    dauer_tage: Optional[int]

@dataclass
class BearbeitungsverlaufDaten:
    """Vorbereitete Daten für den Bearbeitungsverlauf."""
    durchschnitt: Optional[float] = None

    eintraege: List[BearbeitungsverlaufRohEintrag] = field(default_factory=list)
    durchschnitt_verlauf: List[Dict[str, Any]] = field(default_factory=list)

# =====================================================================
# 7) Kursplan
# =====================================================================

@dataclass
class KursplanRohEintrag:
    """Rohdaten eines Eintrags im Kursplan-Gantt-Diagramm."""
    semester: Optional[int]
    kurs_name: str
    kurs_kuerzel: Optional[str]
    plan_start: Optional[date]
    plan_end: Optional[date]
    ist_start: Optional[date]
    ist_end: Optional[date]

@dataclass
class KursplanDaten:
    """Vorbereitete Daten für das Kursplan-Gantt-Diagramm."""
    min_datum: Optional[date] = None
    max_datum: Optional[date] = None
    studium_start: Optional[date] = None
    studium_ende: Optional[date] = None
    
    eintraege: List[KursplanRohEintrag] = field(default_factory=list)
    semester_optionen: List[int] = field(default_factory=list)











