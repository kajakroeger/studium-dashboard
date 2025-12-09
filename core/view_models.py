"""
ViewModels = reine Datenklassen, völlig unabhängig von UI-Technologien.
Sie enthalten KEINE Logik, nur Werte, die im UI angezeigt werden sollen.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, Optional, List


# =====================================================================
# 1) STUDIENZIELE
# =====================================================================

@dataclass
class StudienzieleViewModel:
    """
    Datenmodell für die Anzeige der Studienziele des Studenten.
    """

    ziel_notenschnitt: Optional[float] = None
    ziel_enddatum: Optional[str] = None
    ziel_enddatum_str: Optional[str] = None

    hat_einschreibung: bool = False
    fehlermeldung: Optional[str] = None


# =====================================================================
# 2) STUDIENZIELE STATUS
# =====================================================================

@dataclass
class StudienzieleStatusViewModel:
    """View Model für den Status der Studienziele."""
    # Noten
    aktueller_schnitt: Optional[float]
    ziel_note: Optional[float]
    benoetigte_note_naechster_kurs: Optional[float]
    benoetigter_durchschnitt_rest: Optional[float]
    best_moeglicher_schnitt_naechster_kurs: Optional[float]
    rest_kurse: Optional[int]
    anzahl_noten: int
    
    ziel_erreicht: bool
    hat_ziel_note: bool
    hat_tempo_daten: bool

    ist_tage_pro_5ects: Optional[float]
    ziel_tage_pro_5ects: float
    tempo_abweichung: Optional[float]  

    naechster_besserer_schnitt: Optional[float] = None
    note_fuer_minimale_verbesserung: Optional[float] = None
    prognose_enddatum: Optional[date] = None
    diff_tage_zum_ziel: Optional[int] = None
    fehlermeldung: Optional[str] = None



# =====================================================================
# 3) STATUS-ÜBERSICHT
# =====================================================================

@dataclass
class StatusUebersichtViewModel:
    """
    ViewModel für die Status-Übersichts-Kachel.
    Enthält KEINE UI-Logik und KEINE Service-Aufrufe.
    Nur fertige Daten für die Darstellung.
    """
    
    ects_ziel: Optional[float] = None
    ects_bestanden: Optional[float] = None
    ects_offen: Optional[float] = None
    ects_prozent: Optional[float] = None

    notenschnitt: Optional[float] = None
    bearbeitungszeit_pro_5ects: Optional[float] = None

    hat_studiengang: bool = False
    hat_daten: bool = False
    fehlermeldung: Optional[str] = None



# =====================================================================
# 4) BURNDOWN CHART
# =====================================================================

@dataclass
class BurndownViewModel:
    """
    Struktur für das Burndown Chart.
    """

    monate_labels: List[str] = None
    ideal_verlauf: List[float] = None
    ist_verlauf: List[float] = None
    ist_hover_texte: List[str] = None
    ist_hat_daten_flags: List[bool] = None  # Für Marker / Punkte
    ziel_ects: Optional[float] = None

    start_datum: List[date] = None
    end_datum: List[date] = None

    hat_daten: bool = False
    fehlermeldung: Optional[str] = None



# =====================================================================
# 5) NOTENVERLAUF
# =====================================================================

@dataclass
class NotenverlaufViewModel:
    """
    Enthält den kompletten Datensatz für den Notenverlauf.
    Die UI muss nur noch die Werte visualisieren.
    """

    kursnamen: List[str] = None
    noten: List[float] = None
    pruefungsformen: List[str] = None
    durchschnittsverlauf: List[float] = None
    
    durchschnitt: List[float] = None
    beste_note: List[float] = None
    anzahl_kurse: List[int] = None

    hat_daten: bool = False
    fehlermeldung: Optional[str] = None



# =====================================================================
# 6) BEARBEITUNGSVERLAUF 
# =====================================================================

@dataclass
class BearbeitungsverlaufEintrag:
    kurs_label: str
    start_datum: Optional[date]
    abgabe_datum: Optional[date]
    dauer_tage: Optional[int]
    status_text: str


@dataclass
class BearbeitungsverlaufViewModel:
    eintraege: List[BearbeitungsverlaufEintrag] 
    hat_daten: bool = False
    fehlermeldung: Optional[str] = None
    durchschnitt: Optional[float] = None
    durchschnitt_verlauf: List[Dict[str, Any]] = field(default_factory=list)



# =====================================================================
# 7) KURSPLAN
# =====================================================================

@dataclass
class KursplanEintrag:
    """Ein einzelner Eintrag im Gantt-Chart."""
    semester: int
    kurs_label: str  
    plan_start: Optional[date]
    plan_end: Optional[date]
    ist_start: Optional[date]
    ist_end: Optional[date]

@dataclass
class KursplanViewModel:
    """ ViewModel für das Kursplan-Gantt-Diagramm. """
    eintraege: List[KursplanEintrag] = field(default_factory=list)
    semester_optionen: List[int] = field(default_factory=list)
    min_datum: Optional[date] = None
    max_datum: Optional[date] = None
    studium_start: Optional[date] = None
    studium_ende: Optional[date] = None
    hat_daten: bool = False
    fehlermeldung: Optional[str] = None


