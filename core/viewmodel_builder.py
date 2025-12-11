# core/viewmodel_builder.py
from __future__ import annotations
from datetime import date
from typing import List, Optional, Tuple

from core.dtos import BearbeitungszeitenAnalyse, NotenAnalyse
from core.workflow_service import WorkflowService
from core.progress_service import ProgressService
from models.bearbeitung import StatusBearbeitung
from .view_models import (
    BearbeitungsverlaufEintrag,
    NotenverlaufViewModel,
    BearbeitungsverlaufViewModel,
    StatusUebersichtViewModel,
    BurndownViewModel,
    KursplanViewModel,
    KursplanEintrag,
    StudienzieleViewModel,
    StudienzieleStatusViewModel,
)


class ViewModelBuilder:
    """
    Factory für ViewModels.
    Zentraler Ort für die Daten-Vorbereitung (UI-unabhängig).
    """

    def __init__(
        self,
        *,
        workflow_service: WorkflowService,
        progress_service: ProgressService,
    ) -> None:
        self.workflow = workflow_service
        self.progress = progress_service

        # ✅ Zwei separate Caches
        self._cache_bearbeitung: dict[int, BearbeitungszeitenAnalyse] = {}
        self._cache_noten: dict[int, NotenAnalyse] = {}

    # ---------------------------------------------------------------------
    # Cache-Methoden
    # ---------------------------------------------------------------------

    def _lade_bearbeitungsanalyse(self, student_id: int) -> BearbeitungszeitenAnalyse:
        """
        ✅ FIXED: Gibt jetzt BearbeitungszeitenAnalyse-Objekt zurück!
        """
        if student_id not in self._cache_bearbeitung:
            self._cache_bearbeitung[student_id] = \
                self.progress.bearbeitungszeiten_analyse(student_id)
        return self._cache_bearbeitung[student_id]

    def _lade_notenanalyse(self, student_id: int) -> NotenAnalyse:
        """
        ✅ NEU: Cache für Noten-Analyse.
        """
        if student_id not in self._cache_noten:
            self._cache_noten[student_id] = \
                self.progress.noten_analyse(student_id)
        return self._cache_noten[student_id]

    # =====================================================================
    # 1) Studienziele
    # =====================================================================

    def build_studienziele(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> StudienzieleViewModel:
        try:
            einschreibung = self.workflow.aktive_einschreibung(student_id)
        except Exception as e:
            return StudienzieleViewModel(
                hat_einschreibung=False,
                fehlermeldung=str(e),
            )

        if not einschreibung:
            return StudienzieleViewModel(
                hat_einschreibung=False,
                fehlermeldung="Keine aktive Einschreibung gefunden.",
            )

        ziel_enddatum_str = (
            einschreibung.ziel_enddatum.strftime("%d.%m.%Y")
            if einschreibung.ziel_enddatum
            else None
        )

        return StudienzieleViewModel(
            ziel_enddatum=einschreibung.ziel_enddatum,
            ziel_enddatum_str=ziel_enddatum_str,
            ziel_notenschnitt=einschreibung.ziel_notenschnitt,
            hat_einschreibung=True,
        )

    # =====================================================================
    # 2) Studienziele Status
    # =====================================================================

    def build_studienziele_status(
        self,
        student_id: int,
        ziel_tage_pro_5ects: float = 30.0,
    ) -> StudienzieleStatusViewModel:
        """
        ✅ FIXED: Nutzt beide Caches und übergibt sie an Services!
        """
        try:
            # 🎯 Beide Analysen einmal laden (cached)
            noten_analyse = self._lade_notenanalyse(student_id)
            bearbeitung_analyse = self._lade_bearbeitungsanalyse(student_id)
            
            # Services mit gecachten Daten füttern
            noten_status = self.progress.berechne_notenziel_status(
                student_id,
                noten_analyse=noten_analyse,  # ✅ Cache!
            )
            tempo_status = self.progress.berechne_tempo_status(
                student_id,
                analyse=bearbeitung_analyse,  # ✅ Cache!
                ziel_tage_pro_5ects=ziel_tage_pro_5ects,
            )
            
        except Exception as e:
            print("Fehler in build_studienziele_status:", e)
            import traceback
            traceback.print_exc()
            return StudienzieleStatusViewModel(
                aktueller_schnitt=None,
                ziel_note=None,
                benoetigte_note_naechster_kurs=None,
                benoetigter_durchschnitt_rest=None,
                best_moeglicher_schnitt_naechster_kurs=None,
                rest_kurse=None,
                anzahl_noten=0,
                ziel_erreicht=False,
                ist_tage_pro_5ects=None,
                ziel_tage_pro_5ects=ziel_tage_pro_5ects,
                tempo_abweichung=None,
                prognose_enddatum=None,
                diff_tage_zum_ziel=None,
                hat_ziel_note=False,
                hat_tempo_daten=False,
                fehlermeldung=str(e),
            )

        return StudienzieleStatusViewModel(
            aktueller_schnitt=noten_status.aktueller_schnitt,
            ziel_note=noten_status.ziel_note,
            benoetigte_note_naechster_kurs=noten_status.benoetigte_note_naechster_kurs,
            benoetigter_durchschnitt_rest=noten_status.benoetigter_durchschnitt_rest,
            best_moeglicher_schnitt_naechster_kurs=noten_status.best_moeglicher_schnitt_naechster_kurs,
            rest_kurse=noten_status.rest_kurse,
            anzahl_noten=noten_status.anzahl_noten,
            ziel_erreicht=noten_status.ziel_erreicht,
            ist_tage_pro_5ects=tempo_status.ist_tage_pro_5ects,
            ziel_tage_pro_5ects=ziel_tage_pro_5ects,
            tempo_abweichung=tempo_status.tempo_abweichung,
            prognose_enddatum=tempo_status.prognose_enddatum,
            diff_tage_zum_ziel=tempo_status.diff_tage_zum_ziel,
            hat_ziel_note=(noten_status.ziel_note is not None),
            hat_tempo_daten=(tempo_status.ist_tage_pro_5ects is not None),
            naechster_besserer_schnitt=noten_status.naechster_besserer_schnitt,
            note_fuer_minimale_verbesserung=noten_status.note_fuer_minimale_verbesserung,
            fehlermeldung=None,
        )

    # =====================================================================
    # 3) Status-Übersicht
    # =====================================================================

    def build_status_uebersicht(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> StatusUebersichtViewModel:
        """
        ✅ FIXED: Nutzt beide Caches.
        """
        vm = StatusUebersichtViewModel()

        try:
            # ✅ Analysen aus Cache
            ects = self.progress.ects_analyse(student_id)
            noten = self._lade_notenanalyse(student_id)
            tempo = self._lade_bearbeitungsanalyse(student_id)

            vm.ects_ziel = ects.ects_gesamt
            vm.ects_bestanden = ects.ects_bestanden
            vm.ects_offen = ects.ects_offen
            vm.ects_prozent = ects.ects_prozent
            vm.hat_studiengang = ects.ects_gesamt is not None

            vm.notenschnitt = noten.aktueller_schnitt
            vm.bearbeitungszeit_pro_5ects = tempo.normiert_pro_5ects

            vm.hat_daten = any([
                vm.ects_ziel is not None,
                vm.ects_bestanden is not None,
                vm.notenschnitt is not None,
                vm.bearbeitungszeit_pro_5ects is not None,
            ])

            return vm
        except Exception as e:
            print("Fehler in build_status_uebersicht:", e)
            import traceback
            traceback.print_exc()
            vm.hat_daten = False
            vm.fehlermeldung = str(e)
            return vm

    # =====================================================================
    # 4) Burndown Chart
    # =====================================================================

    def build_burndown_chart(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> BurndownViewModel:
        """
        ✅ FIXED: Nutzt abgeschlossene_bearbeitungen() aus WorkflowService!
        """
        try:
            studiengaenge = self.workflow.studiengaenge_by_student_id(student_id)
            if not studiengaenge:
                return self._empty_burndown("Kein Studiengang gefunden")

            ziel_ects = float(studiengaenge[0].ects_gesamt or 0)
            if ziel_ects <= 0:
                return self._empty_burndown("Kein ECTS-Ziel hinterlegt")

            einschreibung = self.workflow.aktive_einschreibung(student_id)
            if not einschreibung:
                return self._empty_burndown("Keine Einschreibung gefunden")

            start_datum = (
                einschreibung.start_datum.replace(day=1)
                if einschreibung.start_datum
                else date.today().replace(day=1)
            )
            ziel_enddatum = einschreibung.ziel_enddatum

            # ✅ FIXED: Nutzt abgeschlossene_bearbeitungen aus WorkflowService
            abgeschlossene_ab = self.workflow.abgeschlossene_bearbeitungen(student_id)
            abgeschlossene: List[Tuple[date, str, int]] = []

            for ab in abgeschlossene_ab:
                b = ab.bearbeitung
                kurs = ab.kurs
                
                if not b.abgabe_datum:
                    continue
                if not kurs or not getattr(kurs, "ects", None):
                    continue

                name = kurs.name
                ects = int(kurs.ects)
                abgeschlossene.append((b.abgabe_datum, name, ects))

            if not abgeschlossene:
                return self._empty_burndown("Noch keine abgeschlossenen Kurse")

            # Sortieren nach Datum
            abgeschlossene.sort(key=lambda x: x[0])

            # Enddatum bestimmen
            last_completion = max((k[0] for k in abgeschlossene), default=None)

            if ziel_enddatum:
                end_datum = ziel_enddatum
            elif last_completion:
                tmp = last_completion.replace(day=1)
                end_datum = self._add_months(tmp, 1)
            else:
                end_datum = self._add_months(start_datum, 24)

            months = self._generiere_monatsliste(start_datum, end_datum)

            actual_rest, hover_texts, had_flags = self._berechne_ist_kurve(
                months, ziel_ects, abgeschlossene
            )

            total_span = max(len(months) - 1, 1)
            ideal_rest = [
                max(ziel_ects - (ziel_ects * i / total_span), 0)
                for i in range(len(months))
            ]

            monate_labels = [m.strftime("%b %Y") for m in months]

            return BurndownViewModel(
                monate_labels=monate_labels,
                ideal_verlauf=ideal_rest,
                ist_verlauf=actual_rest,
                ist_hover_texte=hover_texts,
                ist_hat_daten_flags=had_flags,
                ziel_ects=ziel_ects,
                start_datum=start_datum,
                end_datum=end_datum,
                hat_daten=True,
                fehlermeldung=None,
            )

        except Exception as e:
            print("Fehler in build_burndown_chart:", e)
            import traceback
            traceback.print_exc()
            return self._empty_burndown(str(e))

    def _empty_burndown(self, fehler: str) -> BurndownViewModel:
        return BurndownViewModel(
            monate_labels=[],
            ideal_verlauf=[],
            ist_verlauf=[],
            ist_hover_texte=[],
            ist_hat_daten_flags=[],
            ziel_ects=0,
            start_datum=date.today(),
            end_datum=date.today(),
            hat_daten=False,
            fehlermeldung=fehler,
        )

    def _generiere_monatsliste(self, start: date, end: date) -> List[date]:
        months: List[date] = []
        cur = start
        while cur <= end:
            months.append(cur)
            cur = self._add_months(cur, 1)
        return months if months else [start]

    def _berechne_ist_kurve(
        self,
        months: List[date],
        ziel_ects: float,
        kurse: List[Tuple[date, str, int]],
    ) -> Tuple[List[float], List[str], List[bool]]:
        actual_rest: List[float] = []
        hover_texts: List[str] = []
        had_flags: List[bool] = []

        verbleibende_ects = ziel_ects
        kurs_idx = 0

        for monat in months:
            monat_str = monat.strftime("%Y-%m")
            kurse_in_monat: List[Tuple[str, int]] = []

            while kurs_idx < len(kurse):
                abgabe, name, ects = kurse[kurs_idx]
                abgabe_monat_str = abgabe.strftime("%Y-%m")

                if abgabe_monat_str == monat_str:
                    verbleibende_ects -= ects
                    kurse_in_monat.append((name, ects))
                    kurs_idx += 1
                elif abgabe_monat_str < monat_str:
                    verbleibende_ects -= ects
                    kurs_idx += 1
                else:
                    break

            verbleibende_ects = max(verbleibende_ects, 0)
            actual_rest.append(verbleibende_ects)
            had_flags.append(len(kurse_in_monat) > 0)

            monat_display = monat.strftime("%b %Y")
            if kurse_in_monat:
                kurse_text = "<br>".join(
                    [f"• {n} ({e} ECTS)" for n, e in kurse_in_monat]
                )
                hover_texts.append(
                    f"<b>{monat_display}</b><br><b>Abgeschlossen:</b><br>{kurse_text}<br>"
                    f"<b>Verbleiben noch {verbleibende_ects:.0f} ECTS</b>"
                )
            else:
                hover_texts.append(
                    f"<b>{monat_display}</b><br>"
                    f"Verbleibende ECTS: {verbleibende_ects:.0f}"
                )

        return actual_rest, hover_texts, had_flags

    def _add_months(self, d: date, months: int) -> date:
        month = d.month - 1 + months
        year = d.year + month // 12
        month = month % 12 + 1
        return date(year, month, 1)

    # =====================================================================
    # 5) Notenverlauf
    # =====================================================================

    def build_notenverlauf(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> NotenverlaufViewModel:
        """
        ✅ OPTIMIERT: Nutzt abgeschlossene_bearbeitungen().
        """
        try:
            bearbeitungen = self.workflow.abgeschlossene_bearbeitungen(student_id)

            kursnamen: List[str] = []
            noten: List[float] = []
            pruefungsformen: List[str] = []

            for ab in bearbeitungen:
                pruefung = ab.pruefung
                kurs = ab.kurs

                if not pruefung or not getattr(pruefung, "bestanden", False):
                    continue
                if pruefung.note is None:
                    continue
                if not kurs:
                    continue

                kuerzel = kurs.kurs_kuerzel or kurs.name
                if len(kuerzel) > 20:
                    kuerzel = kuerzel[:17] + "..."

                kursnamen.append(kuerzel)
                noten.append(float(pruefung.note))

                pf_text = (
                    pruefung.pruefungsform.value
                    if getattr(pruefung, "pruefungsform", None)
                    else "–"
                )
                pruefungsformen.append(pf_text)

            if not noten:
                return NotenverlaufViewModel(
                    kursnamen=[],
                    noten=[],
                    pruefungsformen=[],
                    durchschnittsverlauf=[],
                    durchschnitt=None,
                    beste_note=None,
                    anzahl_kurse=0,
                    hat_daten=False,
                    fehlermeldung="Noch keine Noten vorhanden.",
                )

            # Laufender Durchschnitt
            durchschnittsverlauf: List[float] = []
            total = 0.0
            for i, note in enumerate(noten, start=1):
                total += note
                durchschnittsverlauf.append(total / i)

            return NotenverlaufViewModel(
                kursnamen=kursnamen,
                noten=noten,
                pruefungsformen=pruefungsformen,
                durchschnittsverlauf=durchschnittsverlauf,
                durchschnitt=durchschnittsverlauf[-1],
                beste_note=min(noten),
                anzahl_kurse=len(noten),
                hat_daten=True,
                fehlermeldung=None,
            )

        except Exception as e:
            return NotenverlaufViewModel(
                kursnamen=[],
                noten=[],
                pruefungsformen=[],
                durchschnittsverlauf=[],
                durchschnitt=None,
                beste_note=None,
                anzahl_kurse=0,
                hat_daten=False,
                fehlermeldung=str(e),
            )

    # =====================================================================
    # 6) Bearbeitungsverlauf
    # =====================================================================

    def build_bearbeitungsverlauf(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> BearbeitungsverlaufViewModel:
        """
        ✅ FIXED: Nutzt BearbeitungszeitenAnalyse-Objekt aus Cache.
        """
        try:
            bearbeitungen = self.workflow.bearbeitungen_fuer_student(student_id)

            bearbeitungen = [
                b for b in bearbeitungen
                if getattr(b, "status", None) == StatusBearbeitung.ABGESCHLOSSEN
            ]

            if not bearbeitungen:
                return BearbeitungsverlaufViewModel(
                    eintraege=[],
                    hat_daten=False,
                    fehlermeldung="Noch keine abgeschlossenen Bearbeitungen vorhanden.",
                    durchschnitt=None,
                    durchschnitt_verlauf=[],
                )

            eintraege: List[BearbeitungsverlaufEintrag] = []

            for b in bearbeitungen:
                kurs = self.workflow.kurs_by_id(b.kurs_id)
                if not kurs:
                    continue

                kurs_label = kurs.kurs_kuerzel or kurs.name
                dauer_tage = self.workflow.bearbeitungszeit_in_tagen(b)
                status_text = getattr(b.status, "value", str(b.status))

                eintraege.append(
                    BearbeitungsverlaufEintrag(
                        kurs_label=kurs_label,
                        start_datum=b.start_datum,
                        abgabe_datum=b.abgabe_datum,
                        dauer_tage=dauer_tage,
                        status_text=status_text,
                    )
                )

            if not eintraege:
                return BearbeitungsverlaufViewModel(
                    eintraege=[],
                    hat_daten=False,
                    fehlermeldung="Noch keine Bearbeitungen vorhanden.",
                    durchschnitt=None,
                    durchschnitt_verlauf=[],
                )

            eintraege.sort(key=lambda e: (e.start_datum or date.min, e.kurs_label))

            # ✅ FIXED: Nutzt Objekt-Attribute statt dict-Keys
            analyse = self._lade_bearbeitungsanalyse(student_id)
            
            return BearbeitungsverlaufViewModel(
                eintraege=eintraege,
                hat_daten=True,
                fehlermeldung=None,
                durchschnitt=analyse.durchschnitt_tage,
                durchschnitt_verlauf=analyse.verlauf,
            )

        except Exception as e:
            print("Fehler in build_bearbeitungsverlauf:", e)
            import traceback
            traceback.print_exc()
            return BearbeitungsverlaufViewModel(
                eintraege=[],
                hat_daten=False,
                fehlermeldung=str(e),
                durchschnitt=None,
                durchschnitt_verlauf=[],
            )

    # =====================================================================
    # 7) Kursplan Gantt
    # =====================================================================

    def build_kursplan(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> KursplanViewModel:
        try:
            bearbeitungen = self.workflow.bearbeitungen_fuer_student(student_id)

            eintraege: List[KursplanEintrag] = []

            for b in bearbeitungen:
                kurs = self.workflow.kurs_by_id(b.kurs_id)
                if not kurs:
                    continue

                if not any([b.plan_start, b.plan_end, b.start_datum, b.abgabe_datum]):
                    continue

                kursname = kurs.kurs_kuerzel or kurs.name
                kurs_label = (
                    f"{(kurs.semester or 0)}. Sem – {kursname}"
                    if kurs.semester
                    else kursname
                )

                eintraege.append(
                    KursplanEintrag(
                        semester=kurs.semester,
                        kurs_label=kurs_label,
                        plan_start=b.plan_start,
                        plan_end=b.plan_end,
                        ist_start=b.start_datum,
                        ist_end=b.abgabe_datum,
                    )
                )

            if not eintraege:
                return KursplanViewModel(
                    eintraege=[],
                    semester_optionen=[],
                    min_datum=None,
                    max_datum=None,
                    studium_start=None,
                    studium_ende=None,
                    hat_daten=False,
                    fehlermeldung="Noch keine Daten für den Kursplan vorhanden.",
                )

            semester_optionen = sorted(
                {e.semester for e in eintraege if e.semester is not None}
            )

            alle_datumswerte: List[date] = []
            for e in eintraege:
                for d in [e.plan_start, e.plan_end, e.ist_start, e.ist_end]:
                    if d:
                        alle_datumswerte.append(d)

            min_datum = min(alle_datumswerte) if alle_datumswerte else None
            max_datum = max(alle_datumswerte) if alle_datumswerte else None

            einschreibung = self.workflow.aktive_einschreibung(student_id)
            studium_start = einschreibung.start_datum if einschreibung else None
            studium_ende = einschreibung.ziel_enddatum if einschreibung else None

            return KursplanViewModel(
                eintraege=eintraege,
                semester_optionen=semester_optionen,
                min_datum=min_datum,
                max_datum=max_datum,
                studium_start=studium_start,
                studium_ende=studium_ende,
                hat_daten=True,
                fehlermeldung=None,
            )

        except Exception as e:
            return KursplanViewModel(
                eintraege=[],
                semester_optionen=[],
                min_datum=None,
                max_datum=None,
                studium_start=None,
                studium_ende=None,
                hat_daten=False,
                fehlermeldung=str(e),
            )