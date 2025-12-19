# core/view_models.py
"""
🍽️ TELLER
- enthält die fertige Gerichte

Technisch:
- Datenklassen, unabhängig von UI-Technologie
- enthalten KEINE Logik, nur Werte, die im UI angezeigt werden sollen
- enthalten den kompletten Datensatz für die jeweilige Ansicht
- können Hilfsfelder für die UI enthalten, wie 'hat_daten' oder 'fehlermeldung'
- UI muss nur noch die Werte visualisieren
"""

# Hinweis zu None vs. default_factory:
# - Sammlungen (List/Dict/Set) sollten NICHT None sein, sondern immer existieren.
#   => field(default_factory=list) / field(default_factory=dict)
#   Vorteil: Keine None-Checks nötig; for/len/append funktionieren immer (leere Liste = "keine Daten").
# - Einzelwerte dürfen Optional[...]=None sein, wenn "nicht vorhanden" fachlich sinnvoll ist
#   (z.B. durchschnitt, beste_note, fehlermeldung).

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List


# =====================================================================
# 1) STUDIENZIELE
# =====================================================================

@dataclass
class StudienzieleViewModel:
    """View Model für die Studienziele."""
    ziel_notenschnitt: Optional[float] = None
    ziel_enddatum: Optional[date] = None
    hat_einschreibung: bool = False
    fehlermeldung: Optional[str] = None


# =====================================================================
# 2) STUDIENZIELE STATUS
# =====================================================================

@dataclass
class StudienzieleStatusViewModel:
    """View Model für den Status der Studienziele."""
    aktueller_schnitt: Optional[float] = None
    ziel_note: Optional[float]= None
    benoetigte_note_naechster_kurs: Optional[float]= None
    benoetigter_durchschnitt_rest: Optional[float]= None
    best_moeglicher_schnitt_naechster_kurs: Optional[float]= None
    rest_kurse: Optional[int]= None
    anzahl_noten: int = 0
    
    ziel_erreicht: bool = False
    hat_ziel_note: bool = False
    hat_tempo_daten: bool = False

    ist_tage_pro_5ects: Optional[float]= None
    # TODO: Die aktuelle Dashboard-Version hat statischen Richtwert von statisch auf 30 Tage pro 5 ECTS
    # für die Bearbeitungszeit.Perspektivisch sollte dieser Wert dynamisch berechnet werden,
    # z. B. abhängig von Anzahl der verbleibenden Kurse und dem geplanten Abschlussdatum.
    ziel_tage_pro_5ects: float = 30.0
    tempo_abweichung: Optional[float]= None  

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
    """ViewModel für die Status-Übersichts-Kachel."""
    ects_gesamt: Optional[float] = None
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
    """ViewModel für das Burndown Chart."""
    ziel_ects: Optional[float] = None
    start_datum: Optional[date] = None
    end_datum: Optional[date] = None

    hat_daten: bool = False
    fehlermeldung: Optional[str] = None
    
    monate_labels: List[str] = field(default_factory=list)
    ideal_verlauf: List[float] = field(default_factory=list)
    ist_verlauf: List[float] = field(default_factory=list)
    ist_hover_texte: List[str] = field(default_factory=list)
    ist_hat_daten_flags: List[bool] = field(default_factory=list) 

# =====================================================================
# 5) NOTENVERLAUF
# =====================================================================

@dataclass
class NotenverlaufViewModel:
    """ViewModel für den Notenverlauf"""
    durchschnitt: Optional[float] = None
    beste_note: Optional[float] = None
    anzahl_kurse: int = 0

    hat_daten: bool = False
    fehlermeldung: Optional[str] = None

    kursnamen: List[str] = field(default_factory=list)
    noten: List[float] = field(default_factory=list)
    pruefungsformen: List[str] = field(default_factory=list)
    durchschnittsverlauf: List[float] = field(default_factory=list)

# =====================================================================
# 6) BEARBEITUNGSVERLAUF 
# =====================================================================

@dataclass
class BearbeitungsverlaufEintrag:
    """Ein einzelner Eintrag im Bearbeitungsverlauf."""
    kurs_label: str
    start_datum: Optional[date]
    abgabe_datum: Optional[date]
    dauer_tage: Optional[int]

@dataclass
class DurchschnittVerlaufPunkt:
    index: int
    datum: Optional[date]
    avg_dauer_tage: float


@dataclass
class BearbeitungsverlaufViewModel:
    """ViewModel für den Bearbeitungsverlauf."""
    hat_daten: bool = False
    fehlermeldung: Optional[str] = None
    durchschnitt: Optional[float] = None
    
    durchschnitt_verlauf: List[DurchschnittVerlaufPunkt]= field(default_factory=list)
    eintraege: List[BearbeitungsverlaufEintrag] = field(default_factory=list)

# =====================================================================
# 7) KURSPLAN
# =====================================================================

@dataclass
class KursplanEintrag:
    """Ein einzelner Eintrag im Gantt-Chart."""
    semester: Optional[int]
    kurs_label: str  
    plan_start: Optional[date]
    plan_end: Optional[date]
    ist_start: Optional[date]
    ist_end: Optional[date]

@dataclass
class KursplanViewModel:
    """ViewModel für das Kursplan-Gantt-Diagramm. """
    min_datum: Optional[date] = None
    max_datum: Optional[date] = None
    studium_start: Optional[date] = None
    studium_ende: Optional[date] = None
    hat_daten: bool = False
    fehlermeldung: Optional[str] = None

    eintraege: List[KursplanEintrag] = field(default_factory=list)
    semester_optionen: List[int] = field(default_factory=list)

