# core/progress_service.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

from core.dtos import (
    BearbeitungszeitenAnalyse, 
    EctsAnalyse, 
    NotenAnalyse, 
    NotenZielStatus, 
    TempoStatus
)
from core.workflow_service import WorkflowService
from models.bearbeitung import StatusBearbeitung


class ProgressService:
    """
    Verantwortlich für:
    - Analysen über Noten
    - Analysen über ECTS-Fortschritt
    - Analysen über Bearbeitungszeiten
    - zusammengesetzte Ziel-Status (NotenZielStatus, TempoStatus)
    """

    def __init__(self, workflow: WorkflowService) -> None:
        self._wf = workflow

    # ---------------------------------------------------------------------
    # Hilfsfunktionen
    # ---------------------------------------------------------------------

    def alle_bestandenen_noten(self, student_id: int) -> List[float]:
        """Holt alle Noten der bestandenen Prüfungen."""
        noten: List[float] = []
        for ab in self._wf.abgeschlossene_bearbeitungen(student_id):
            if not ab.pruefung:
                continue
            if not getattr(ab.pruefung, "bestanden", False):
                continue
            if ab.pruefung.note is None:
                continue
            noten.append(float(ab.pruefung.note))
        return noten

    # ---------------------------------------------------------------------
    # Noten-Analyse
    # ---------------------------------------------------------------------

    def noten_analyse(self, student_id: int) -> NotenAnalyse:
        """
        Fasst alle Noteninfos zusammen:
        - aktueller Schnitt
        - beste Note
        - Anzahl Noten
        - Liste der Noten
        """
        noten = self.alle_bestandenen_noten(student_id)

        if not noten:
            return NotenAnalyse(
                aktueller_schnitt=None,
                beste_note=None,
                anzahl_noten=0,
                noten_liste=[],
            )

        aktueller_schnitt = round(sum(noten) / len(noten), 2)
        beste = min(noten)

        return NotenAnalyse(
            aktueller_schnitt=aktueller_schnitt,
            beste_note=beste,
            anzahl_noten=len(noten),
            noten_liste=noten,
        )

    def berechne_notenschnitt(self, student_id: int) -> Optional[float]:
        """Kompatible Kurzform für bisherigen Code."""
        return self.noten_analyse(student_id).aktueller_schnitt

    # ---------------------------------------------------------------------
    # ECTS-Analyse
    # ---------------------------------------------------------------------

    def ects_analyse(self, student_id: int) -> EctsAnalyse:
        """Analysiert den ECTS-Fortschritt."""
        # 1) ECTS-Gesamt aus Studiengang
        studiengaenge = self._wf.studiengaenge_by_student_id(student_id)
        sg = studiengaenge[0] if studiengaenge else None
        ects_gesamt: Optional[float] = None
        if sg and getattr(sg, "ects_gesamt", None) is not None:
            ects_gesamt = float(sg.ects_gesamt)

        # 2) ECTS aus abgeschlossenen Kursen
        ects_bestanden = 0.0
        for ab in self._wf.abgeschlossene_bearbeitungen(student_id):
            if not ab.kurs or not getattr(ab.kurs, "ects", None):
                continue
            ects_bestanden += float(ab.kurs.ects)

        # 3) Offen & Prozent
        ects_offen: Optional[float] = None
        ects_prozent: Optional[float] = None
        if ects_gesamt is not None:
            ects_offen = max(ects_gesamt - ects_bestanden, 0.0)
            if ects_gesamt > 0:
                ects_prozent = min(
                    max(ects_bestanden / ects_gesamt * 100.0, 0.0),
                    100.0,
                )

        return EctsAnalyse(
            ects_gesamt=ects_gesamt,
            ects_bestanden=ects_bestanden,
            ects_offen=ects_offen,
            ects_prozent=ects_prozent,
        )

    def ects_summe_bestanden(self, student_id: int) -> float:
        """Kompatible Kurzform für bisherigen Code."""
        return self.ects_analyse(student_id).ects_bestanden

    # ---------------------------------------------------------------------
    # Bearbeitungszeiten-Analyse
    # ---------------------------------------------------------------------

    def bearbeitungszeiten_analyse(
        self,
        student_id: int,
        normierung_ects: float = 5.0
    ) -> BearbeitungszeitenAnalyse:
        """
        ✅ FIXED: Gibt jetzt BearbeitungszeitenAnalyse-Objekt zurück!
        
        Zentrale Analyse aller Bearbeitungszeiten.
        Liefert:
        - durchschnitt_tage
        - normiert_pro_5ects
        - verlauf (Timeline)
        - anzahl_kurse
        - erreichte_ects (für Tempo-Prognose)
        - verbleibende_ects
        """
        bearbeitungen = self._wf.bearbeitungen_fuer_student(student_id)

        daten = []
        for b in bearbeitungen:
            if b.status != StatusBearbeitung.ABGESCHLOSSEN:
                continue

            tage = self._wf.bearbeitungszeit_in_tagen(b)
            if tage is None:
                continue

            kurs = self._wf.kurs_by_id(b.kurs_id)
            if not kurs or not kurs.ects:
                continue

            daten.append({
                "tage": tage,
                "ects": kurs.ects,
                "datum": b.abgabe_datum or b.start_datum,
            })

        if not daten:
            return BearbeitungszeitenAnalyse(
                durchschnitt_tage=None,
                normiert_pro_5ects=None,
                verlauf=[],
                anzahl_kurse=0,
                erreichte_ects=0.0,
                verbleibende_ects=None,
            )

        # Durchschnitt (roh)
        durchschnitt = sum(d["tage"] for d in daten) / len(daten)

        # Normiert auf 5 ECTS
        normierte_zeiten = [
            d["tage"] * (normierung_ects / d["ects"])
            for d in daten
        ]
        normiert = sum(normierte_zeiten) / len(normierte_zeiten)

        # Verlauf
        daten.sort(key=lambda d: d["datum"])
        verlauf = []
        summe = 0.0
        for idx, d in enumerate(daten, 1):
            summe += d["tage"]
            verlauf.append({
                "index": idx,
                "datum": d["datum"],
                "avg_dauer_tage": summe / idx,
            })

        # ✅ ECTS berechnen
        erreichte_ects = sum(d["ects"] for d in daten)
        
        # Verbleibende ECTS
        studiengaenge = self._wf.studiengaenge_by_student_id(student_id)
        sg = studiengaenge[0] if studiengaenge else None
        ects_gesamt = float(getattr(sg, "ects_gesamt", 0) or 0.0)
        verbleibende_ects = max(ects_gesamt - erreichte_ects, 0.0) if ects_gesamt > 0 else None

        return BearbeitungszeitenAnalyse(
            durchschnitt_tage=round(durchschnitt, 1),
            normiert_pro_5ects=round(normiert, 1),
            verlauf=verlauf,
            anzahl_kurse=len(daten),
            erreichte_ects=erreichte_ects,
            verbleibende_ects=verbleibende_ects,
        )

    # ---------------------------------------------------------------------
    # Notenziel-Status (für Studienziele-Kachel)
    # ---------------------------------------------------------------------

    def berechne_notenziel_status(
        self,
        student_id: int,
        noten_analyse: Optional[NotenAnalyse] = None,  # ✅ Cache-Support
    ) -> NotenZielStatus:
        """
        Berechnet alle Infos rund um Notenziele für die Studienziele-Kachel.
        
        Args:
            student_id: ID des Studenten
            noten_analyse: Optional gecachte Notenanalyse (Performance)
        """
        # Noten-Daten (aus Cache oder neu berechnen)
        if noten_analyse is None:
            noten_analyse = self.noten_analyse(student_id)
        
        aktueller_schnitt = noten_analyse.aktueller_schnitt
        noten = noten_analyse.noten_liste
        anzahl_noten = noten_analyse.anzahl_noten

        einschreibung = self._wf.aktive_einschreibung(student_id)
        ziel_note = einschreibung.ziel_notenschnitt if einschreibung else None

        # Studiengang für anzahl_kurse
        studiengaenge = self._wf.studiengaenge_by_student_id(student_id)
        sg = studiengaenge[0] if studiengaenge else None
        gesamt_kurse = sg.anzahl_kurse if sg else None

        rest_kurse: Optional[int] = None
        if gesamt_kurse is not None:
            rest_kurse = max(gesamt_kurse - anzahl_noten, 0)

        benoetigte_note_naechster_kurs: Optional[float] = None
        benoetigter_durchschnitt_rest: Optional[float] = None
        best_moeglicher_schnitt: Optional[float] = None
        ziel_erreicht = False
        note_fuer_minimale_verbesserung: Optional[float] = None
        naechster_besserer_schnitt: Optional[float] = None

        if ziel_note is not None and anzahl_noten > 0:
            gesamt_noten = sum(noten)
            best_moeglicher_schnitt = (gesamt_noten + 1.0) / (anzahl_noten + 1)

            # Note, um direkt die Zielnote zu erreichen
            direkte_note = self._note_fuer_ziel_schnitt(
                gesamt_noten=gesamt_noten,
                anzahl_noten=anzahl_noten,
                ziel_schnitt=ziel_note,
            )
            benoetigte_note_naechster_kurs = direkte_note

            # Durchschnitt in restlichen Kursen
            if gesamt_kurse is not None and rest_kurse and rest_kurse > 0:
                required_avg = (ziel_note * gesamt_kurse - gesamt_noten) / rest_kurse
                if required_avg <= 5.0:
                    if required_avg < 1.0:
                        required_avg = 1.0
                    benoetigter_durchschnitt_rest = round(required_avg, 2)

        # Ziel erreicht?
        if aktueller_schnitt is not None and ziel_note is not None:
            ziel_erreicht = aktueller_schnitt <= ziel_note

        # Minimale Note zur Verbesserung
        if aktueller_schnitt is not None and anzahl_noten > 0:
            note_fuer_minimale_verbesserung = self._benoetigte_note_fuer_verbesserung(
                aktueller_schnitt=aktueller_schnitt
            )
            naechster_besserer_schnitt = round(aktueller_schnitt - 0.1, 1)

        return NotenZielStatus(
            aktueller_schnitt=aktueller_schnitt,
            ziel_note=ziel_note,
            benoetigte_note_naechster_kurs=benoetigte_note_naechster_kurs,
            benoetigter_durchschnitt_rest=benoetigter_durchschnitt_rest,
            best_moeglicher_schnitt_naechster_kurs=best_moeglicher_schnitt,
            rest_kurse=rest_kurse,
            anzahl_noten=anzahl_noten,
            ziel_erreicht=ziel_erreicht,
            naechster_besserer_schnitt=naechster_besserer_schnitt,
            note_fuer_minimale_verbesserung=note_fuer_minimale_verbesserung,
        )

    def _note_fuer_ziel_schnitt(
        self,
        *,
        gesamt_noten: float,
        anzahl_noten: int,
        ziel_schnitt: float,
    ) -> Optional[float]:
        """Berechnet die Note für den Zielschnitt."""
        raw = ziel_schnitt * (anzahl_noten + 1) - gesamt_noten
        needed = round(raw * 10) / 10.0
        if needed < 1.0 or needed > 5.0:
            return None
        return needed

    def _benoetigte_note_fuer_verbesserung(
        self,
        *,
        aktueller_schnitt: float,
    ) -> Optional[float]:
        """Berechnet Note für Verbesserung."""
        ziel = max(1.0, round(aktueller_schnitt - 0.1, 1))
        return ziel

    # ---------------------------------------------------------------------
    # Tempo-Status (für Studienziele)
    # ---------------------------------------------------------------------

    def berechne_tempo_status(
        self,
        student_id: int,
        ziel_tage_pro_5ects: float = 30.0,
        analyse: Optional[BearbeitungszeitenAnalyse] = None,  # ✅ Cache-Support
    ) -> TempoStatus:
        """
        ✅ FIXED: Nutzt jetzt BearbeitungszeitenAnalyse-Objekt!
        
        Args:
            student_id: ID des Studenten
            ziel_tage_pro_5ects: Ziel-Tempo
            analyse: Optional gecachte Bearbeitungsanalyse (Performance)
        """
        # Analyse aus Cache oder neu berechnen
        if analyse is None:
            analyse = self.bearbeitungszeiten_analyse(student_id, normierung_ects=5.0)

        ist_tage = analyse.normiert_pro_5ects
        tempo_abweichung: Optional[float] = None
        if ist_tage is not None:
            tempo_abweichung = ist_tage - ziel_tage_pro_5ects

        einschreibung = self._wf.aktive_einschreibung(student_id)
        
        if not einschreibung or not einschreibung.start_datum:
            return TempoStatus(
                ist_tage_pro_5ects=ist_tage,
                ziel_tage_pro_5ects=ziel_tage_pro_5ects,
                tempo_abweichung=tempo_abweichung,
                prognose_enddatum=None,
                diff_tage_zum_ziel=None,
            )

        start = einschreibung.start_datum
        ziel_enddatum = einschreibung.ziel_enddatum

        # ✅ FIXED: Nutzt analyse.erreichte_ects aus Objekt
        if analyse.erreichte_ects <= 0 or analyse.verbleibende_ects is None:
            return TempoStatus(
                ist_tage_pro_5ects=ist_tage,
                ziel_tage_pro_5ects=ziel_tage_pro_5ects,
                tempo_abweichung=tempo_abweichung,
                prognose_enddatum=None,
                diff_tage_zum_ziel=None,
            )

        # ECTS pro Tag
        heute = date.today()
        tage_vergangen = max((heute - start).days, 1)
        ects_pro_tag = analyse.erreichte_ects / tage_vergangen

        if ects_pro_tag <= 0 or analyse.verbleibende_ects == 0.0:
            prognose_enddatum = heute
        else:
            rest_tage = analyse.verbleibende_ects / ects_pro_tag
            prognose_enddatum = heute + timedelta(days=round(rest_tage))

        diff_tage: Optional[int] = None
        if ziel_enddatum:
            diff_tage = (prognose_enddatum - ziel_enddatum).days

        return TempoStatus(
            ist_tage_pro_5ects=ist_tage,
            ziel_tage_pro_5ects=ziel_tage_pro_5ects,
            tempo_abweichung=tempo_abweichung,
            prognose_enddatum=prognose_enddatum,
            diff_tage_zum_ziel=diff_tage,
        )