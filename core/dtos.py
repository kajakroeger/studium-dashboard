"""
core/dtos.py
Gemeinsame Datenklassen/DTOs, die von mehreren Services genutzt werden.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from models.bearbeitung import Bearbeitung
from models.kurs import Kurs
from models.pruefung import Pruefung


@dataclass
class NotenZielStatus:
    """DTO für Studienziele Status für den Fortschritt der Noten."""
    aktueller_schnitt: Optional[float]
    ziel_note: Optional[float]
    benoetigte_note_naechster_kurs: Optional[float]
    benoetigter_durchschnitt_rest: Optional[float]
    best_moeglicher_schnitt_naechster_kurs: Optional[float]
    rest_kurse: Optional[int]
    anzahl_noten: int
    ziel_erreicht: bool
    naechster_besserer_schnitt: Optional[float] = None
    note_fuer_minimale_verbesserung: Optional[float] = None

@dataclass
class TempoStatus:
    """DTO für Studienziele Status für den Fortschritt der Bearbeitungen."""
    ist_tage_pro_5ects: Optional[float]
    ziel_tage_pro_5ects: float
    tempo_abweichung: Optional[float]
    prognose_enddatum: Optional[date]
    diff_tage_zum_ziel: Optional[int]

@dataclass
class BearbeitungszeitenAnalyse:
    durchschnitt_tage: Optional[float]
    normiert_pro_5ects: Optional[float]
    verlauf: List[Dict]
    anzahl_kurse: int
    erreichte_ects: float
    verbleibende_ects: Optional[float]

@dataclass
class EctsAnalyse:
    ects_gesamt: Optional[float]
    ects_bestanden: float
    ects_offen: Optional[float]
    ects_prozent: Optional[float]

@dataclass
class NotenAnalyse:
    aktueller_schnitt: Optional[float]
    beste_note: Optional[float]
    anzahl_noten: int
    noten_liste: List[float]

@dataclass
class AbgeschlosseneBearbeitung:
    """
    Hilfsobjekt für Analysen:
    kombinierte Sicht auf Bearbeitung + Kurs + Prüfung.
    """
    bearbeitung: Bearbeitung
    kurs: Kurs
    pruefung: Optional[Pruefung]









