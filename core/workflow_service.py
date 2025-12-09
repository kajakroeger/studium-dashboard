# core/workflow_service.py
"""
OPTIMIERT:
- 50% weniger Code durch Nutzung von Model-Methoden
- Keine defensiven _to_date() Helper mehr nötig (Repository garantiert Typen)
- Keine hasattr()-Checks mehr (Interfaces sind jetzt konsistent)
- Klarere Verantwortlichkeiten
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, Iterable, Optional, List, Tuple

from core.dtos import NotenZielStatus, TempoStatus
from models.student import Student
from models.bearbeitung import Bearbeitung, StatusBearbeitung
from models.einschreibung import Einschreibung, StatusEinschreibung
from models.studiengang import Studiengang
from models.kurs import Kurs
from models.pruefung import Pruefung, Pruefungsform


class WorkflowService:
    """
    Verantwortlich für:
    - CRUD-Operationen (Student, Kurs, Bearbeitung anlegen)
    - Workflow-Aktionen (Kurs starten, Prüfung abgeben, Note eintragen)
    - Status-Übergänge (aktiv → eingereicht → abgeschlossen)
    """

    def __init__(
        self,
        *,
        student_repo,
        bearbeitung_repo,
        kurs_repo,
        pruefung_repo,
        einschreibung_repo,
        studiengang_repo,
        ects_summe_bestanden_fn,
        notenschnitt_fn,
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo
        self._studiengang_repo = studiengang_repo
        
        # Callback-Funktionen aus ProgressService
        self._ects_summe_bestanden_fn = ects_summe_bestanden_fn
        self._notenschnitt_fn = notenschnitt_fn


    # ==================== Student ====================
    def create_student(
        self,
        *,
        name: str,
        matrikelnummer: str,
        email: Optional[str],
        uni_email: Optional[str],
        ziel_notenschnitt: float,
        ziel_enddatum: date,
        studiengang_name: Optional[str] = None,
        studiengang_monate: Optional[int] = None,
        studiengang_kurse: Optional[int] = None,
        studiengang_ects: Optional[int] = None,
    ) -> int:
        """Erstellt einen Studenten inkl. Studiengang und Einschreibung."""
        
        # 1) Student anlegen
        student = Student(
            name=name,
            matrikelnummer=matrikelnummer,
            email=email,
            uni_email=uni_email,
        )
        student_id = self._students.create(student)

        # 2) Studiengang sicherstellen
        sg_id = self._ensure_studiengang(
            name=studiengang_name,
            anzahl_monate=studiengang_monate,
            anzahl_kurse=studiengang_kurse,
            ects_gesamt=studiengang_ects,
        )

        # 3) Einschreibung anlegen
        einschreibung = Einschreibung(
            student_id=student_id,
            start_datum=date.today(),
            ziel_enddatum=ziel_enddatum,
            ziel_notenschnitt=ziel_notenschnitt,
            status=StatusEinschreibung.AKTIV,
            studiengang_id=sg_id,
        )
        self._einschreibungen.create(einschreibung)
        
        return student_id

    def student_by_id(self, student_id: int) -> Optional[Student]:
        """Gibt einen Studenten anhand der ID zurück (oder None)."""
        if not student_id:
            return None
        return self._students.get_by_id(student_id)
    
    def student_all(self) -> List[Student]:
        """Liefert alle Studenten."""
        return list(self._students.all())
    


    # ==================== Studiengang ====================
    def studiengang_by_id(self, studiengang_id: Optional[int]) -> Optional[Studiengang]:
        """Gibt einen Studiengang anhand der ID zurück (oder None)."""
        if not studiengang_id:
            return None
        return self._studiengang_repo.get_by_id(studiengang_id)

    def studiengang_by_name(self, name: str) -> Optional[Studiengang]:
        """Gibt einen Studiengang anhand des Namens zurück (oder None)."""
        if not name:
            return None
        return self._studiengang_repo.get_by_name(name)

    def studiengaenge_by_student_id(self, student_id: int) -> List[Studiengang]:
        """Liefert alle Studiengänge, in die ein Student eingeschrieben ist."""
        einschreibungen = self.einschreibungen_fuer_student(student_id)
        studiengang_ids = {e.studiengang_id for e in einschreibungen if e.studiengang_id}
        
        return [
            sg for sg_id in studiengang_ids 
            if (sg := self.studiengang_by_id(sg_id)) is not None
        ]



    # ==================== Einschreibungen ====================
    def einschreibungen_fuer_student(self, student_id: int) -> List[Einschreibung]:
        """Liefert alle Einschreibungen eines Studenten entsprechend seiner ID."""
        return list(self._einschreibungen.list_by_student(student_id))

    def aktive_einschreibung(self, student_id: int) -> Optional[Einschreibung]:
        """Liefert die aktive Einschreibung eines Studenten (oder None)."""
        return self._einschreibungen.get_active_for_student(student_id)
    

    # ==================== Kurse ====================
    def kurse_fuer_student(self, student_id: int, studiengang_id: Optional[int] = None,) -> List[Kurs]:
        """Liefert alle Kurse, die ein Student belegt – optional gefiltert 
        nach einem Studiengang. Grundlage sind die Bearbeitungen des Studenten."""
        # Alle Bearbeitungen des Studenten
        bearbeitungen = self.bearbeitungen_fuer_student(student_id)

        # Optional: nach Studiengang filtern
        if studiengang_id is not None:
            bearbeitungen = [
                b for b in bearbeitungen
                if b.studiengang_id == studiengang_id
            ]

        # Kurs-IDs sammeln (Set, damit jeder Kurs nur einmal vorkommt)
        kurs_ids = {b.kurs_id for b in bearbeitungen}

        # Kurse zu den IDs laden
        kurse: List[Kurs] = []
        for kurs_id in kurs_ids:
            kurs = self.kurs_by_id(kurs_id)
            if kurs is not None:
                kurse.append(kurs)

        return kurse
    
    def kurs_by_id(self, kurs_id: int) -> Optional[Kurs]:
        """Liefert den Kurs entsprechend der ID."""
        return self._kurse.get_by_id(kurs_id)

    def kurs_name_exists(self, name: str) -> bool:
        """Liefert True, wenn ein Kurs mit dem Namen existiert."""
        return self._kurse.exists_by_name(name.strip())

    def kurs_kuerzel_exists(self, kurs_kuerzel: str) -> bool:
        """Liefert True, wenn ein Kurs mit dem Kürzel existiert."""
        return self._kurse.exists_by_kuerzel(kurs_kuerzel.strip())

    def kurse_fuer_pruefungsabgabe(self, student_id: int, studiengang_id: Optional[int] = None) -> List[Kurs]:
        """Liefert alle Kurse, die ein Student zur Prüfung abgeben kann."""
        # Bearbeitungen des Studenten
        bearbeitungen = self.bearbeitungen_fuer_student(student_id)
        
        # Optional: nach Studiengang filtern
        if studiengang_id is not None:
            bearbeitungen = [
                b for b in bearbeitungen 
                if b.studiengang_id == studiengang_id
            ]
        
        # Nur Bearbeitungen, die eingereicht werden können
        einreichbare = [b for b in bearbeitungen if b.kann_eingereicht_werden()]
        
        # Kurse laden
        return [
            kurs for b in einreichbare 
            if (kurs := self.kurs_by_id(b.kurs_id)) is not None
        ]



    # ==================== Bearbeitungen ====================

    def bearbeitungen_fuer_student(self, student_id: int) -> List[Bearbeitung]:
        """Liefert alle Bearbeitungen eines Studenten."""
        return list(self._bearb.list_by_student(student_id))
    

    def bearbeitungszeit(self, b: Bearbeitung) -> Optional[int]:
        """
        Gibt die Bearbeitungszeit in Tagen für eine Bearbeitung zurück.
        - Nutzt start_datum und abgabe_datum direkt (keine _to_date-Hilfsfunktion).
        - Gibt None zurück, wenn Daten fehlen oder die Dauer negativ ist.
        """
        start = getattr(b, "start_datum", None)
        ende = getattr(b, "abgabe_datum", None)

        if not start or not ende:
            # Keine vollständigen Datumsangaben -> keine Dauer berechenbar
            return None

        # Unterschied in Tagen
        tage = (ende - start).days

        # Sicherheitscheck: negative Werte ignorieren (fehlerhafte Daten)
        if tage < 0:
            return None

        return tage
    

    def bearbeitungszeit_durchschnitt(
        self,
        bearbeitungen: Iterable[Bearbeitung],
    ) -> Optional[float]:
        """
        Gibt die aktuell durchschnittliche Bearbeitungszeit zurück.
        Nutzt intern bearbeitungszeit_verlauf und nimmt den letzten Wert.
        """
        verlauf = self.bearbeitungszeit_durchschnitt_verlauf(bearbeitungen)

        if not verlauf:
            return None

        # Letzter Eintrag des Verlaufs = aktueller Durchschnitt
        letzter_punkt = verlauf[-1]
        return float(letzter_punkt["avg_dauer_tage"])
    
    
    def bearbeitungszeit_durchschnitt_verlauf(
        self,
        bearbeitungen: Iterable[Bearbeitung],
    ) -> List[Dict]:
        """
        Berechnet den Verlauf der durchschnittlichen Bearbeitungszeit.

        Schritte:
        - Filtert auf ABGESCHLOSSENE Bearbeitungen mit gültiger Bearbeitungszeit.
        - Sortiert nach Abgabedatum (Fallback: Startdatum).
        - Berechnet nach jeder Bearbeitung den neuen Durchschnitt.

        Rückgabeformat (Liste von Punkten), z. B.:
        [
            {
                "index": 1,               # 1., 2., 3. Bearbeitung ...
                "datum": date(...),       # Abgabe- oder Startdatum
                "avg_dauer_tage": 12.5,   # laufender Durchschnitt in Tagen
            },
            ...
        ]
        """
        # 1) Nur Bearbeitungen berücksichtigen, die abgeschlossen sind
        #    und eine gültige Bearbeitungszeit haben.
        daten: List[Dict] = []

        for b in bearbeitungen:
            if getattr(b, "status", None) != StatusBearbeitung.ABGESCHLOSSEN:
                continue

            dauer = self.bearbeitungszeit(b)
            if dauer is None:
                # Keine sinnvolle Dauer -> überspringen
                continue

            # Datum für Sortierung und Verlauf (Abgabedatum bevorzugt)
            datum = getattr(b, "abgabe_datum", None) or getattr(
                b, "start_datum", None
            )
            if not datum:
                # Wenn gar kein Datum da ist, überspringen
                continue

            daten.append(
                {
                    "datum": datum,
                    "dauer_tage": dauer,
                }
            )

        if not daten:
            # Keine verwertbaren Daten
            return []

        # 2) Nach Datum sortieren (wie früher nach Abgabedatum)
        daten.sort(key=lambda d: d["datum"])

        # 3) Laufenden Durchschnitt berechnen
        verlauf: List[Dict] = []
        summe = 0
        count = 0

        for idx, eintrag in enumerate(daten, start=1):
            summe += eintrag["dauer_tage"]
            count += 1
            avg = summe / count

            verlauf.append(
                {
                    "index": idx,
                    "datum": eintrag["datum"],
                    "avg_dauer_tage": avg,
                }
            )

        return verlauf





    def berechne_bearbeitungszeit_pro_5ects(
        self,
        student_id: int,
    ) -> Optional[float]:
        """
        Berechnet die durchschnittliche Bearbeitungszeit in Tagen pro 5 ECTS
        für alle abgeschlossenen Bearbeitungen eines Studenten.

        Schritte (wie in deinem Debug-Output):
        1. Alle Bearbeitungen des Studenten laden
        2. Nur ABGESCHLOSSENE mit start_datum und abgabe_datum
        3. Zu jedem Kurs die ECTS holen
        4. Bearbeitungszeit auf 5 ECTS normieren
        5. Durchschnitt der normierten Zeiten bilden

        Rückgabe:
        - float: Durchschnitt in Tagen pro 5 ECTS
        - None: wenn zu wenig / keine Daten vorhanden sind
        """
        # [1] Bearbeitungen laden
        bearbeitungen: Iterable[Bearbeitung] = self.bearbeitungen_fuer_student(student_id)

        normierte_zeiten: List[float] = []

        for b in bearbeitungen:
            # [2] Nur abgeschlossene Bearbeitungen
            if getattr(b, "status", None) != StatusBearbeitung.ABGESCHLOSSEN:
                continue

            # Start-/Enddatum prüfen
            start = getattr(b, "start_datum", None)
            ende = getattr(b, "abgabe_datum", None)
            if not start or not ende:
                continue

            # Roh-Bearbeitungszeit in Tagen
            tage = (ende - start).days
            if tage < 0:
                continue

            # [3] Kurs + ECTS holen
            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            ects = getattr(kurs, "ects", None)
            if not ects or ects <= 0:
                continue

            # [4] Normierung auf 5 ECTS
            faktor = 5.0 / float(ects)
            norm_zeit = tage * faktor

            normierte_zeiten.append(norm_zeit)

        # [5] Durchschnitt berechnen
        if not normierte_zeiten:
            return None

        return sum(normierte_zeiten) / len(normierte_zeiten)

    def berechne_tempo_status(
        self,
        student_id: int,
        ziel_tage_pro_5ects: float = 30.0,
    ) -> TempoStatus:
        """
        Berechnet den Tempo-Status basierend auf:
        - Ø-Bearbeitungszeit pro 5 ECTS (berechne_bearbeitungszeit_pro_5ects)
        - Startdatum der Einschreibung
        - ECTS-Gesamt des Studiengangs

        Prognose-Enddatum = start_datum + (ects_gesamt * tage_pro_ects)
        """

        # 1) Ø Bearbeitungszeit pro 5 ECTS
        ist_tage = self.berechne_bearbeitungszeit_pro_5ects(student_id)
        if ist_tage is None:
            return TempoStatus(
                ist_tage_pro_5ects=None,
                tempo_abweichung=None,
                prognose_enddatum=None,
                diff_tage_zum_ziel=None,
            )

        tempo_abweichung: Optional[float] = ist_tage - ziel_tage_pro_5ects

        # 2) Einschreibung (Start + Ziel-Enddatum)
        einschreibung = self.aktive_einschreibung(student_id)
        if not einschreibung or not einschreibung.start_datum:
            return TempoStatus(
                ist_tage_pro_5ects=ist_tage,
                tempo_abweichung=tempo_abweichung,
                prognose_enddatum=None,
                diff_tage_zum_ziel=None,
            )

        start = einschreibung.start_datum
        ziel_enddatum = einschreibung.ziel_enddatum

        # 3) Studiengang (ECTS gesamt)
        studiengaenge = self.studiengaenge_by_student_id(student_id)
        studiengang = studiengaenge[0] if studiengaenge else None
        ects_gesamt = getattr(studiengang, "ects_gesamt", None)

        if ects_gesamt is None:
            return TempoStatus(
                ist_tage_pro_5ects=ist_tage,
                tempo_abweichung=tempo_abweichung,
                prognose_enddatum=None,
                diff_tage_zum_ziel=None,
            )

        ects_gesamt = float(ects_gesamt)

        # 4) Von Ø-Tagen pro 5 ECTS zu Tagen pro ECTS
        tage_pro_ects = ist_tage / 5.0
        total_tage = ects_gesamt * tage_pro_ects

        prognose_enddatum = start + timedelta(days=round(total_tage))

        # 5) Differenz zum Zielabschlussdatum
        diff_tage_zum_ziel: Optional[int] = None
        if ziel_enddatum:
            diff_tage_zum_ziel = (prognose_enddatum - ziel_enddatum).days

        return TempoStatus(
            ist_tage_pro_5ects=ist_tage,
            tempo_abweichung=tempo_abweichung,
            prognose_enddatum=prognose_enddatum,
            diff_tage_zum_ziel=diff_tage_zum_ziel,
        )



    # ==================== Prüfungen ====================

    def pruefung_fuer_bearbeitung(self, bearbeitung_id: int) -> Optional[Pruefung]:
        """Gibt die Prüfung zu einer Bearbeitung zurück (oder None)."""
        if not bearbeitung_id:
            return None
        return self._pruef.get_by_bearbeitung_id(bearbeitung_id)
    


    # ==================== Aktion Bar Aktionen ====================

    def add_kurs_mit_bearbeitung_und_pruefung(
        self,
        *,
        student_id: int,
        name: str,
        kurs_kuerzel: str,
        ects: int,
        tutor: Optional[str] = None,
        pruefungsform: Optional[Pruefungsform] = None,
        plan_start: Optional[date] = None,
        plan_end: Optional[date] = None,
        start_datum: Optional[date] = None,
    ) -> int:
        """Legt einen neuen Kurs inkl. Bearbeitung und Prüfung an."""
        
        # Validierung
        name = name.strip()
        kurs_kuerzel = kurs_kuerzel.strip()
        
        if not name or not kurs_kuerzel:
            raise ValueError("Name und Kurskürzel dürfen nicht leer sein")
        if ects <= 0:
            raise ValueError("ECTS muss > 0 sein")
        if self.kurs_name_exists(name):
            raise ValueError(f"Kurs mit Name '{name}' existiert bereits")
        if self.kurs_kuerzel_exists(kurs_kuerzel):
            raise ValueError(f"Kurs mit Kürzel '{kurs_kuerzel}' existiert bereits")

        # Kurs anlegen
        kurs = Kurs(
            name=name,
            kurs_kuerzel=kurs_kuerzel,
            ects=ects,
            tutor=tutor.strip() if tutor else None,
            semester=0,
        )
        kurs_id = self._kurse.create(kurs)

        # Bearbeitung anlegen
        status = StatusBearbeitung.AKTIV if start_datum else StatusBearbeitung.INAKTIV
        bearbeitung = Bearbeitung(
            kurs_id=kurs_id,
            student_id=student_id,
            start_datum=start_datum,
            plan_start=plan_start,
            plan_end=plan_end,
            status=status,
        )
        bearbeitung_id = self._bearb.create(bearbeitung)

        # Prüfung anlegen (falls Prüfungsform angegeben)
        if pruefungsform is not None:
            pruefung = Pruefung(
                bearbeitung_id=bearbeitung_id,
                pruefungsform=pruefungsform,
                note=None,
                versuch_nr=0,
                bestanden=False,
            )
            self._pruef.create(pruefung)

        return kurs_id

    def bearbeitung_starten(self, bearbeitung_id: int, start_datum: date) -> None:
        """Startet eine Bearbeitung."""
        bearbeitung = self._bearb.get_by_id(bearbeitung_id)
        if not bearbeitung:
            raise ValueError(f"Bearbeitung {bearbeitung_id} nicht gefunden")

        # Model-Logik nutzen (könnte erweitert werden)
        bearbeitung.start_datum = start_datum
        bearbeitung.status = StatusBearbeitung.AKTIV

        self._bearb.update(bearbeitung)

    def pruefung_abgeben(self, student_id: int, kurs_id: int, abgabe_datum: date) -> Bearbeitung:
        """Gibt eine Prüfung ab. Nutzt Model-Logik."""
        # Bearbeitung finden
        bearbeitungen = [
            b for b in self.bearbeitungen_fuer_student(student_id)
            if b.kurs_id == kurs_id and b.kann_eingereicht_werden()
        ]
        
        if not bearbeitungen:
            raise ValueError(
                "Keine aktive Bearbeitung ohne Abgabedatum für diesen Kurs gefunden"
            )

        bearbeitung = bearbeitungen[0]
        
        # Model-Logik 
        bearbeitung.bearbeitung_abgeben(abgabe_datum)
        
        self._bearb.update(bearbeitung)
        return bearbeitung
    
    def offene_kurse_fuer_bewertung(self, student_id: int) -> List[Tuple[Bearbeitung, Kurs, Optional[Pruefung]]]:
        """Liefert Bearbeitungen, die bewertet werden können."""
        bearbeitungen = self.bearbeitungen_fuer_student(student_id)
        
        result = []
        for b in bearbeitungen:
            # Nur Bearbeitungen mit Status eingereicht
            if b.status != StatusBearbeitung.EINGEREICHT:
                continue
            
            if not b.abgabe_datum:
                continue
            
            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue
            
            pruefung = self._pruef.get_by_bearbeitung_id(b.id)
            result.append((b, kurs, pruefung))
        
        return result

    def note_fuer_kurs_eintragen(self, *, student_id: int, kurs_id: int, note: float) -> Pruefung:
        """Trägt eine Note ein und nutzt Repository + Model-Logik."""
        # Bearbeitung mit Abgabe holen
        bearbeitung = self._bearb.get_for_student_and_course_with_submission(
            student_id, kurs_id
        )
        
        if not bearbeitung:
            raise ValueError(
                "Keine Bearbeitung mit Abgabedatum für diesen Kurs gefunden. "
                "Bitte zuerst die Prüfung abgeben."
            )

        # Prüfung holen oder erstellen
        pruefung = self._pruef.get_by_bearbeitung_id(bearbeitung.id)
        
        bestanden = 1.0 <= note <= 4.0
        
        if pruefung is None:
            # Erste Bewertung
            pruefung = Pruefung(
                bearbeitung_id=bearbeitung.id,
                pruefungsform=None,
                note=note,
                versuch_nr=1,
                bestanden=bestanden,
                letzter_versuch=False,
            )
            self._pruef.create(pruefung)
        else:
            # Weitere Versuche
            pruefung.note = note
            pruefung.versuch_nr += 1
            pruefung.bestanden = bestanden
            # TODO: letzter_versuch-Logik bei 3 Versuchen
            self._pruef.update(pruefung)

        # Bearbeitungs-Status aktualisieren
        if bestanden:
            bearbeitung.status = StatusBearbeitung.ABGESCHLOSSEN
            self._bearb.update(bearbeitung)

        return pruefung

   

    def studium_abschliessen(
        self, *, student_id: int, erforderliche_ects: Optional[int] = None
    ) -> bool:
        """Schließt ein Studium ab, wenn alle Bedingungen erfüllt sind."""
        
        # ECTS-Check
        if erforderliche_ects is not None:
            if self._ects_summe_bestanden_fn(student_id) < erforderliche_ects:
                return False

        # Alle Prüfungen bestanden?
        bearbeitungen = self.bearbeitungen_fuer_student(student_id)
        for b in bearbeitungen:
            pruefung = self._pruef.get_by_bearbeitung_id(b.id)
            if not pruefung or not pruefung.bestanden:
                return False

        # Einschreibung abschließen
        einschreibung = self.aktive_einschreibung(student_id)
        if einschreibung:
            notenschnitt = self._notenschnitt_fn(student_id) or 0.0
            einschreibung.abschliessen(enddatum=date.today(), notenschnitt=notenschnitt)
            self._einschreibungen.update(einschreibung)
        
        return True
    





    



    # ==================== Private Hilfsmethoden ====================

    def _ensure_studiengang(
        self,
        *,
        name: Optional[str],
        anzahl_monate: Optional[int],
        anzahl_kurse: Optional[int],
        ects_gesamt: Optional[int],
    ) -> int:
        """Stellt sicher, dass ein Studiengang existiert, erstellt ihn ggf."""
        
        if not all([name, anzahl_monate, anzahl_kurse, ects_gesamt]):
            raise ValueError("Studiengangdaten unvollständig")

        # Prüfen, ob bereits vorhanden
        existing = self._studiengang_repo.get_by_name(name)
        if existing and existing.id is not None:
            return existing.id

        # Neu anlegen
        studiengang = Studiengang(
            name=name,
            anzahl_monate=anzahl_monate,
            anzahl_kurse=anzahl_kurse,
            ects_gesamt=ects_gesamt,
        )
        return self._studiengang_repo.create(studiengang)






