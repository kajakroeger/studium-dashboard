from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Optional

from core.dtos import (
    AbgeschlosseneBearbeitung,
    BearbeitungsverlaufDaten,
    BearbeitungsverlaufRohEintrag,
    BurndownDaten,
    KursplanDaten,
    KursplanRohEintrag,
    NotenverlaufDaten,
    StatusUebersichtDaten,
    StudienzieleDaten,
    StudienzieleStatusDaten,
)
from core.workflow_service import WorkflowService
from models.bearbeitung import Bearbeitung
from models.einschreibung import Einschreibung
from models.studiengang import Studiengang


@dataclass
class _StudentContext:
    """
    Interner Snapshot für genau einen Studenten und einen Studiengang.

    - Viele Dashboard-Kacheln benötigen ähnliche Daten (Bearbeitungen, Kurse, Prüfungen, Ziele).
    - Ohne Context würden mehrere Methoden dieselben DB-/Service-Aufrufe wiederholen.
    - Der Context wird daher einmal geladen und im ProgressService gecached.

    Hinweis:
    - Der Context ist bewusst intern, weil er kein offizieller Teil der API ist.
    - Typen sind hier bewusst generisch gehalten (object), weil die Daten aus WorkflowService stammen
      und sich das zugrunde liegende Model-Design ändern kann, ohne dass der ProgressService sofort bricht.
    """
    student_id: int
    studiengang_id: int

    einschreibung: Optional[Einschreibung]
    studiengang: Optional[Studiengang]

    bearbeitungen: list[Bearbeitung]
    abgeschlossene: list[AbgeschlosseneBearbeitung]


class ProgressService:
    """
    🧑‍🍳 KOCH
    - Holt die Zutaten aus dem Lager (Rohdaten aus dem WorkflowService)
      und bereitet sie für die gewünschten Gerichte (Dashboard-Kacheln) auf.
    - Packt die vorbereiteten Gerichte in Boxen (DTOs) 

    Technisch:
    - Bereitet ALLE Daten für die Kacheln vor
    - Lädt Rohdaten EINMAL via _context() (Cache)
    - Gibt nur *_daten() DTOs zurück
    - ViewModelBuilder nutzt NUR diese Methoden
    """

    def __init__(self, workflow: WorkflowService) -> None:
        self._wf = workflow

        # Cache pro student_id und studiengang_id:
        # UI ruft pro Render mehrere Kacheln ab -> Context wird damit nur einmal geladen
        self._ctx_cache: dict[tuple[int, Optional[int]], _StudentContext] = {}

    # =====================================================================
    # 1) Studienziele-Daten
    # =====================================================================

    def studienziele_daten(self, student_id: int, studiengang_id: int) -> Optional[StudienzieleDaten]:
        """
        Liefert die gesetzten Ziele eines Studenten.
        Rückgabe None: Wenn keine aktive Einschreibung existiert (z.B. Student noch nicht eingeschrieben).
        """
        ctx = self._context(student_id, studiengang_id)  
        e = ctx.einschreibung
        if not e:
            return None

        return StudienzieleDaten(
            ziel_notenschnitt=e.ziel_notenschnitt,
            ziel_enddatum=e.ziel_enddatum,
            start_datum=e.start_datum,
        )


    # =====================================================================
    # 2) Studienziele-Status-Daten
    # =====================================================================

    def studienziele_status_daten(
        self,
        student_id: int,
        studiengang_id: int, 
        ziel_tage_pro_5ects: float = 30.0,
    ) -> StudienzieleStatusDaten:
        """
        Liefert Daten über den aktuellen Stand bezüglich der Studienziele.

        - Noten-Status (Schnitt, Ziel, benötigte Note etc.)
        - Tempo-Status (normiert auf 5 ECTS)
        """
        ctx = self._context(student_id, studiengang_id)

        e = ctx.einschreibung
        sg = ctx.studiengang 

        # ---------------------------------------------------------------------
        # A) NOTEN
        # ---------------------------------------------------------------------
        noten_liste: list[float] = []
        for ab in ctx.abgeschlossene:
            p = ab.pruefung                    # Optional[Pruefung]
            if p is None or p.bestanden is not True:
                continue
            if p.note is None:
                continue
            noten_liste.append(float(p.note))

        anzahl_noten = len(noten_liste)
        aktueller_schnitt: Optional[float] = (
            round(sum(noten_liste) / anzahl_noten, 2) if anzahl_noten > 0 else None
        )

        ziel_note: Optional[float] = e.ziel_notenschnitt if e else None

        gesamt_kurse: Optional[int] = sg.anzahl_kurse if sg else None
        rest_kurse: Optional[int] = (
            max(gesamt_kurse - anzahl_noten, 0) if gesamt_kurse is not None else None
        )

        benoetigte_note_naechster_kurs: Optional[float] = None
        benoetigter_durchschnitt_rest: Optional[float] = None
        best_moeglicher_schnitt: Optional[float] = None
        ziel_erreicht = False
        note_fuer_minimale_verbesserung: Optional[float] = None
        naechster_besserer_schnitt: Optional[float] = None

        if ziel_note is not None and anzahl_noten > 0:
            gesamt_noten = sum(noten_liste)

            # Best-Case: nächste Note wäre 1.0
            best_moeglicher_schnitt = round((gesamt_noten + 1.0) / (anzahl_noten + 1), 2)

            # Note für Ziel im nächsten Kurs (sofern im gültigen Notenbereich)
            raw = ziel_note * (anzahl_noten + 1) - gesamt_noten
            needed = round(raw * 10) / 10.0
            if 1.0 <= needed <= 5.0:
                benoetigte_note_naechster_kurs = needed

            # Durchschnitt für restliche Kurse
            if gesamt_kurse is not None and rest_kurse is not None and rest_kurse > 0:
                required_avg = (ziel_note * gesamt_kurse - gesamt_noten) / rest_kurse
                if required_avg <= 5.0:
                    benoetigter_durchschnitt_rest = round(max(required_avg, 1.0), 2)

        if aktueller_schnitt is not None and ziel_note is not None:
            ziel_erreicht = aktueller_schnitt <= ziel_note

        if aktueller_schnitt is not None and anzahl_noten > 0:
            note_fuer_minimale_verbesserung = max(1.0, round(aktueller_schnitt - 0.1, 1))
            naechster_besserer_schnitt = round(aktueller_schnitt - 0.1, 1)

        # ---------------------------------------------------------------------
        # B) TEMPO (normiert auf 5 ECTS)
        # ---------------------------------------------------------------------
        tempo_daten = self._abgeschlossen_tempo_daten(ctx)

        ist_tage_pro_5ects: Optional[float] = None
        tempo_abweichung: Optional[float] = None

        if tempo_daten:
            normierte_zeiten = [d["tage"] * (5.0 / d["ects"]) for d in tempo_daten]
            ist_tage_pro_5ects = round(sum(normierte_zeiten) / len(normierte_zeiten), 1)
            tempo_abweichung = round(ist_tage_pro_5ects - ziel_tage_pro_5ects, 1)

        # ---------------------------------------------------------------------
        # C) PROGNOSE-ENDDATUM (heuristisch)
        # ---------------------------------------------------------------------
        prognose_enddatum: Optional[date] = None
        diff_tage_zum_ziel: Optional[int] = None

        if tempo_daten and e and e.start_datum:
            erreichte_ects = sum(d["ects"] for d in tempo_daten)
            ects_gesamt = float(sg.ects_gesamt) if sg else 0.0
            verbleibende_ects = max(ects_gesamt - erreichte_ects, 0.0) if ects_gesamt > 0 else 0.0

            heute = date.today()
            tage_vergangen = max((heute - e.start_datum).days, 1)
            ects_pro_tag = erreichte_ects / tage_vergangen if erreichte_ects > 0 else 0.0

            if verbleibende_ects > 0 and ects_pro_tag > 0:
                rest_tage = verbleibende_ects / ects_pro_tag
                prognose_enddatum = heute + timedelta(days=round(rest_tage))
            else:
                prognose_enddatum = heute

            if e.ziel_enddatum and prognose_enddatum:
                diff_tage_zum_ziel = (prognose_enddatum - e.ziel_enddatum).days

        return StudienzieleStatusDaten(
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
            ist_tage_pro_5ects=ist_tage_pro_5ects,
            ziel_tage_pro_5ects=ziel_tage_pro_5ects,
            tempo_abweichung=tempo_abweichung,
            prognose_enddatum=prognose_enddatum,
            diff_tage_zum_ziel=diff_tage_zum_ziel,
        )


    # =====================================================================
    # 3) Status-Übersicht-Daten
    # =====================================================================

    def status_uebersicht_daten(self, student_id: int, studiengang_id) -> StatusUebersichtDaten:
        """Liefert die Daten für die Status-Übersicht (ECTS + Noten + Tempo) und gibt es als DTO StatusUebersichtDaten zurück."""
        ctx = self._context(student_id, studiengang_id)

        # ---------------------------------------------------------------------
        # A) ECTS
        # ---------------------------------------------------------------------
        sg = ctx.studiengang
        ects_gesamt = float(sg.ects_gesamt) if sg else None

         # ECTS: abgeschlossene Kurse
        ects_bestanden = sum(float(ab.kurs.ects) for ab in ctx.abgeschlossene)

        ects_offen = None
        ects_prozent = None
        if ects_gesamt is not None and ects_gesamt > 0:
            ects_offen = max(ects_gesamt - ects_bestanden, 0.0)
            ects_prozent = min(max((ects_bestanden / ects_gesamt) * 100.0, 0.0), 100.0)

        # ---------------------------------------------------------------------
        # B) Noten (bestandene Prüfungen)
        # ---------------------------------------------------------------------
        noten = [
            float(ab.pruefung.note)
            for ab in ctx.abgeschlossene
            if ab.pruefung and ab.pruefung.bestanden is True and ab.pruefung.note is not None
        ]
        notenschnitt = round(sum(noten) / len(noten), 2) if noten else None
        beste_note = min(noten) if noten else None
        anzahl_noten = len(noten)

        # ---------------------------------------------------------------------
        # C) Tempo (abgeschlossene Bearbeitungen, normiert auf 5 ECTS)
        # ---------------------------------------------------------------------
        tempo_daten = self._abgeschlossen_tempo_daten(ctx)
        if not tempo_daten:
            bearbeitungszeit_pro_5ects = None
            durchschnitt_tage = None
        else:
            durchschnitt_tage = round(sum(d["tage"] for d in tempo_daten) / len(tempo_daten), 1)
            normierte = [d["tage"] * (5.0 / d["ects"]) for d in tempo_daten]
            bearbeitungszeit_pro_5ects = round(sum(normierte) / len(normierte), 1)

        return StatusUebersichtDaten(
            ects_gesamt=ects_gesamt,
            ects_bestanden=ects_bestanden,
            ects_offen=ects_offen,
            ects_prozent=ects_prozent,
            notenschnitt=notenschnitt,
            beste_note=beste_note,
            anzahl_noten=anzahl_noten,
            bearbeitungszeit_pro_5ects=bearbeitungszeit_pro_5ects,
            durchschnitt_tage=durchschnitt_tage,
        )


    # =====================================================================
    # 4) Burndown-Daten
    # =====================================================================

    def burndown_daten(self, student_id: int, studiengang_id: int) -> BurndownDaten:
        """Liefert die Daten für das Burndwon Chart und gibt es als DTO BurndownDaten zurück."""
        ctx = self._context(student_id, studiengang_id)

        kurse_mit_datum = [
            (ab.bearbeitung.abgabe_datum, ab.kurs.name, int(ab.kurs.ects))
            for ab in ctx.abgeschlossene
            if ab.bearbeitung.abgabe_datum
        ]
        kurse_mit_datum.sort(key=lambda x: x[0])

        sg = ctx.studiengang
        ziel_ects = float(sg.ects_gesamt) if sg else 0.0

        e = ctx.einschreibung
        start_datum = e.start_datum if e else date.today()
        ziel_enddatum = e.ziel_enddatum if e else None

        return BurndownDaten(
            ziel_ects=ziel_ects,
            start_datum=start_datum,
            ziel_enddatum=ziel_enddatum,
            abgeschlossene_kurse=kurse_mit_datum,
        )


    # =====================================================================
    # 5) Notenverlauf-Daten
    # =====================================================================
    def notenverlauf_daten(self, student_id: int, studiengang_id: int) -> NotenverlaufDaten:
        """Liefert die Daten für den Notenverlauf und gibt es als DTO NotenverlaufDaten zurück."""
        ctx = self._context(student_id, studiengang_id)

        kursnamen: list[str] = []
        noten: list[float] = []
        pruefungsformen: list[str] = []

        # ctx.abgeschlossene ist bei dir bereits studiengang-spezifisch (kommt gefiltert aus WorkflowService)
        for ab in ctx.abgeschlossene:
            p = ab.pruefung
            if p is None:
                continue
            if p.bestanden is not True:
                continue
            if p.note is None:
                continue

            kursnamen.append(ab.kurs.short_label)  # oder ab.kurs.name, je nachdem
            noten.append(float(p.note))
            pruefungsformen.append(p.pruefungsform.value if p.pruefungsform else "–")

        # Verlauf des Notenschnitts berechnen
        durchschnittsverlauf: list[float] = []
        total = 0.0
        for i, note in enumerate(noten, start=1):
            total += note
            durchschnittsverlauf.append(round(total / i, 2))

        return NotenverlaufDaten(
            kursnamen=kursnamen,
            noten=noten,
            pruefungsformen=pruefungsformen,
            durchschnittsverlauf=durchschnittsverlauf,
            aktueller_schnitt=durchschnittsverlauf[-1] if durchschnittsverlauf else None,
            beste_note=min(noten) if noten else None,
        )

    # =====================================================================
    # 6) Bearbeitungsverlauf-Daten
    # =====================================================================

    def bearbeitungsverlauf_daten(self, student_id: int, studiengang_id: int) -> BearbeitungsverlaufDaten:
        """Liefert die Daten für den Bearbeitungsverlauf und gibt es als DTO BearbeitungsverlaufDaten zurück."""
        ctx = self._context(student_id, studiengang_id)

        tempo_daten = self._abgeschlossen_tempo_daten(ctx)

        # Einträge direkt aus tempo_daten bauen:
        eintraege = [
            BearbeitungsverlaufRohEintrag(
                kurs_name=d.get("kurs_name") or "–",
                kurs_kuerzel=d.get("kurs_kuerzel"),
                start_datum=d.get("start_datum"),  
                abgabe_datum=d.get("datum"),
                dauer_tage=int(d["tage"]),
            )
            for d in tempo_daten
        ]

        if not tempo_daten:
            return BearbeitungsverlaufDaten(eintraege=eintraege, durchschnitt=None, durchschnitt_verlauf=[])

        # Verlauf sortieren & Durchschnittsverlauf berechnen (wie bisher)
        tempo_daten.sort(key=lambda d: d["datum"] or date.min)
        durchschnitt = sum(d["tage"] for d in tempo_daten) / len(tempo_daten)

        verlauf = []
        summe = 0.0
        for idx, d in enumerate(tempo_daten, start=1):
            summe += d["tage"]
            verlauf.append({"index": idx, "datum": d["datum"], "avg_dauer_tage": summe / idx})

        return BearbeitungsverlaufDaten(
            eintraege=eintraege,
            durchschnitt=round(durchschnitt, 1),
            durchschnitt_verlauf=verlauf,
        )

    # =====================================================================
    # 7) Kursplan-Daten
    # =====================================================================

    def kursplan_daten(self, student_id: int, studiengang_id: Optional[int] = None) -> KursplanDaten:
        """Liefert Kursplan-Daten und gibt es als DTO KursplanDaten zurück."""
        ctx = self._context(student_id, studiengang_id)

        eintraege = []
        alle_datumswerte = []

        # A) Bearbeitungen laden
        for b in ctx.bearbeitungen:
            kurs = self._wf.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            # Skip wenn Bearbeitung keine Plan/Ist-Daten hat 
            if not any([b.plan_start, b.plan_end, b.start_datum, b.abgabe_datum]):
                continue

            # B) Daten für einen Eintrags im Kursplan-Gantt-Diagramm in KursplanRohEintrag-DTO 
            e = KursplanRohEintrag(
                semester=kurs.semester,
                kurs_name=kurs.name,
                kurs_kuerzel=kurs.kurs_kuerzel,
                plan_start=b.plan_start,
                plan_end=b.plan_end,
                ist_start=b.start_datum,
                ist_end=b.abgabe_datum,
            )
            eintraege.append(e)

            # C) Datumswerte sammeln
            for d in [e.plan_start, e.plan_end, e.ist_start, e.ist_end]:
                if d:
                    alle_datumswerte.append(d)

        # Semester-Optionen
        semester_optionen = sorted({e.semester for e in eintraege if e.semester is not None})

        # Studium Start/Ende
        e = ctx.einschreibung
        studium_start = e.start_datum if e else None
        studium_ende = e.ziel_enddatum if e else None

        # D) Alles gesammelt und berechnet in KursplanDaten-DTO geben
        return KursplanDaten(
            eintraege=eintraege,
            min_datum=min(alle_datumswerte) if alle_datumswerte else None,
            max_datum=max(alle_datumswerte) if alle_datumswerte else None,
            studium_start=studium_start,
            studium_ende=studium_ende,
            semester_optionen=semester_optionen,
        )

    # =====================================================================
    # Helper
    # =====================================================================

    def _abgeschlossen_tempo_daten(self, ctx: _StudentContext) -> list[dict[str, Any]]:
        """Sammelt Tempo-Daten aus abgeschlossenen Bearbeitungen (bearbeitung + kurs sind schon gejoint)."""
        tempo: list[dict[str, Any]] = []

        for ab in ctx.abgeschlossene:
            b = ab.bearbeitung
            kurs = ab.kurs

            tage = self._wf.bearbeitungszeit_in_tagen(b)
            if tage is None:
                continue

            ects = float(kurs.ects)
            if ects <= 0:
                continue

            tempo.append({
                "tage": float(tage),
                "ects": ects,
                "datum": b.abgabe_datum or b.start_datum,
                "kurs_name": kurs.name,
                "kurs_kuerzel": kurs.kurs_kuerzel,
                "start_datum": b.start_datum,
                "abgabe_datum": b.abgabe_datum,
                "status": b.status,
            })

        return tempo

    # =====================================================================
    # Zentraler Context-Loader (Cache)
    # =====================================================================

    def _context(self, student_id: int, studiengang_id: int) -> _StudentContext:
        """
        Lädt alle benötigten Daten für (Student, Studiengang) einmalig und cached sie.

        Warum:
        - Ein Dashboard-Render ruft mehrere Kacheln auf.
        - Kacheln sollen aber *studiengang-spezifische* Daten zeigen.
        - Daher Cache-Key = (student_id, studiengang_id).
        """
        key = (student_id, studiengang_id)


        # A) Cache-Hit
        if key in self._ctx_cache:
            return self._ctx_cache[key]

        # B) Domain-/Workflow-Logik: gewählten Studiengang + passende Einschreibung holen
        sg = self._wf.selected_studiengang(student_id, studiengang_id)
        e = self._wf.aktive_einschreibung(student_id, studiengang_id)

        # C) Bearbeitungen/Abschlüsse studiengang-spezifisch laden
        # Wichtig: Dafür brauchst du *gefilterte* Workflow-Methoden (siehe unten).
        bearbeitungen = self._wf.bearbeitungen_fuer_student(student_id, studiengang_id)
        abgeschlossene = self._wf.abgeschlossene_bearbeitungen(student_id, studiengang_id)

        ctx = _StudentContext(
            student_id=student_id,
            studiengang_id=studiengang_id,
            einschreibung=e,
            studiengang=sg,
            bearbeitungen=bearbeitungen,
            abgeschlossene=abgeschlossene,
        )

        self._ctx_cache[key] = ctx
        return ctx

    def invalidate_cache(
        self,
        student_id: Optional[int] = None,
        studiengang_id: Optional[int] = None,
    ) -> None:
        """
        Cache leeren:
        - Ohne Parameter: alles löschen
        - Nur student_id: alle Studiengänge dieses Studenten löschen
        - student_id + studiengang_id: gezielt einen Cache-Eintrag löschen
        """
        if student_id is None and studiengang_id is None:
            self._ctx_cache.clear()
            return

        if student_id is not None and studiengang_id is not None:
            self._ctx_cache.pop((student_id, studiengang_id), None)
            return

        # nur student_id gesetzt -> alle Keys dieses Studenten entfernen
        if student_id is not None:
            keys_to_delete = [k for k in self._ctx_cache.keys() if k[0] == student_id]
            for k in keys_to_delete:
                self._ctx_cache.pop(k, None)
