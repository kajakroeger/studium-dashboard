from __future__ import annotations
from datetime import date
from typing import List, Optional, Tuple

from core.progress_service import ProgressService

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
    💁‍♂️🍽️ PORTIONIERER
    - nimmt vorbereitete Gerichte aus dem Kühlschrank (DTOs der ProgressServices)
    - richtet sie für den Gast an:
       - übersetzt DTOs in ViewModels
       - ergänzt UI-spezifische Felder (Flags, Texte, Formatierungen)

    - Bindeglied zwischen Fachlogik (ProgressService) und Darstellung (UI)
    - sorgt dafür, dass die UI ausschließlich mit ViewModels arbeitet

    Technisch:
    - ruft ausschließlich *_daten()-Methoden des ProgressService auf
    - erzeugt ViewModels (keine DTOs, keine Models)
    - enthält KEINE Geschäftslogik (keine Berechnungen von Noten/ECTS)
    - enthält KEINE Datenbankzugriffe
    - enthält leichte Präsentationslogik:
      - Flags wie hat_daten / hat_ziel / hat_einschreibung
      - Texte für leere Zustände
      - Listen/Strukturen passend für Charts & Tabellen
    """
    def __init__(
        self,
        *,
        progress_service: ProgressService,
    ) -> None:
        self.progress = progress_service

    # =====================================================================
    # 1) Studienziele
    # =====================================================================

    def build_studienziele(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> StudienzieleViewModel:
        try:
            daten = self.progress.studienziele_daten(student_id, studiengang_id)
            if not daten:
                return StudienzieleViewModel(
                    hat_einschreibung=False,
                    fehlermeldung="Keine aktive Einschreibung gefunden.",
                )

            ziel_enddatum = daten.ziel_enddatum

            return StudienzieleViewModel(
                ziel_notenschnitt=daten.ziel_notenschnitt,
                ziel_enddatum=ziel_enddatum,
                hat_einschreibung=True,
                fehlermeldung=None,
            )

        except Exception as e:
            return StudienzieleViewModel(
                hat_einschreibung=False,
                fehlermeldung=str(e),
            )

    # =====================================================================
    # 2) Studienziele Status
    # =====================================================================

    def build_studienziele_status(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
        ziel_tage_pro_5ects: float = 30.0,
    ) -> StudienzieleStatusViewModel:
        """
        
        """
        try:
            daten = self.progress.studienziele_status_daten(
                student_id,
                studiengang_id,
                ziel_tage_pro_5ects=ziel_tage_pro_5ects,
            )

            return StudienzieleStatusViewModel(
                # Noten-Felder 
                aktueller_schnitt=daten.aktueller_schnitt,
                ziel_note=daten.ziel_note,
                benoetigte_note_naechster_kurs=daten.benoetigte_note_naechster_kurs,
                benoetigter_durchschnitt_rest=daten.benoetigter_durchschnitt_rest,
                best_moeglicher_schnitt_naechster_kurs=daten.best_moeglicher_schnitt_naechster_kurs,
                rest_kurse=daten.rest_kurse,
                anzahl_noten=daten.anzahl_noten,
                ziel_erreicht=daten.ziel_erreicht,
                naechster_besserer_schnitt=daten.naechster_besserer_schnitt,
                note_fuer_minimale_verbesserung=daten.note_fuer_minimale_verbesserung,
                
                # Tempo-Felder 
                ist_tage_pro_5ects=daten.ist_tage_pro_5ects,
                ziel_tage_pro_5ects=daten.ziel_tage_pro_5ects,
                tempo_abweichung=daten.tempo_abweichung,
                prognose_enddatum=daten.prognose_enddatum,
                diff_tage_zum_ziel=daten.diff_tage_zum_ziel,
                
                # Flags
                hat_ziel_note=(daten.ziel_note is not None),
                hat_tempo_daten=(daten.ist_tage_pro_5ects is not None),
                
                fehlermeldung=None,
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
                hat_ziel_note=False,
                hat_tempo_daten=False,
                ist_tage_pro_5ects=None,
                ziel_tage_pro_5ects=ziel_tage_pro_5ects,
                tempo_abweichung=None,
                prognose_enddatum=None,
                diff_tage_zum_ziel=None,
                naechster_besserer_schnitt=None,
                note_fuer_minimale_verbesserung=None,
                fehlermeldung=str(e),
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
        ✅ FIXED: Greift direkt auf flache Felder von StatusUebersichtDaten zu.
        Keine verschachtelten Objekte mehr (kein .ects, .noten, .tempo)!
        """
        vm = StatusUebersichtViewModel()
        
        try:
            daten = self.progress.status_uebersicht_daten(student_id, studiengang_id)

            # ✅ Direkte Feld-Zugriffe (flaches DTO!)
            vm.ects_gesamt = daten.ects_gesamt
            vm.ects_bestanden = daten.ects_bestanden
            vm.ects_offen = daten.ects_offen
            vm.ects_prozent = daten.ects_prozent

            vm.notenschnitt = daten.notenschnitt
            vm.bearbeitungszeit_pro_5ects = daten.bearbeitungszeit_pro_5ects

            vm.hat_studiengang = (daten.ects_gesamt is not None)
            vm.hat_daten = any(
                v is not None
                for v in [
                    vm.ects_gesamt,
                    vm.ects_bestanden,
                    vm.notenschnitt,
                    vm.bearbeitungszeit_pro_5ects,
                ]
            )

            vm.fehlermeldung = None
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

    def build_burndown_chart(self, student_id: int, studiengang_id: Optional[int]) -> BurndownViewModel:
        """
        Holt Rohdaten aus ProgressService, macht nur noch UI-Kurve/Labels.
        """
        try:
            daten = self.progress.burndown_daten(student_id, studiengang_id)

            if not daten.abgeschlossene_kurse:
                return self._empty_burndown("Noch keine abgeschlossenen Kurse")

            if not daten.ziel_ects or daten.ziel_ects <= 0:
                return self._empty_burndown("Kein ECTS-Ziel hinterlegt")

            # Enddatum robust bestimmen:
            # - wenn ziel_enddatum vorhanden -> nehmen
            # - sonst -> letzter Abschluss-Monat + 1 Monat
            # - fallback -> start + 24 Monate
            if daten.ziel_enddatum:
                end = daten.ziel_enddatum
            else:
                last = max((d for (d, _, _) in daten.abgeschlossene_kurse), default=None)
                if last:
                    end = self._add_months(last.replace(day=1), 1)
                else:
                    end = self._add_months(daten.start_datum.replace(day=1), 24)

            start = daten.start_datum.replace(day=1)
            months = self._generiere_monatsliste(start, end)

            actual_rest, hover_texts, had_flags = self._berechne_ist_kurve(
                months, daten.ziel_ects, daten.abgeschlossene_kurse
            )

            # Ideal-Kurve: von ziel_ects linear bis 0 (len-1 Schritte)
            span = max(len(months) - 1, 1)
            ideal_rest = [max(daten.ziel_ects - (daten.ziel_ects * i / span), 0) for i in range(len(months))]

            return BurndownViewModel(
                monate_labels=[m.strftime("%b %Y") for m in months],
                ideal_verlauf=ideal_rest,
                ist_verlauf=actual_rest,
                ist_hover_texte=hover_texts,
                ist_hat_daten_flags=had_flags,
                ziel_ects=daten.ziel_ects,
                start_datum=start,
                end_datum=end,
                hat_daten=True,
                fehlermeldung=None,
            )
        except Exception as e:
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
        cur = start.replace(day=1)
        end = end.replace(day=1)
        while cur <= end:
            months.append(cur)
            cur = self._add_months(cur, 1)
        return months if months else [start.replace(day=1)]

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
                    # falls kurse unsortiert reinkommen (safety)
                    verbleibende_ects -= ects
                    kurs_idx += 1
                else:
                    break

            verbleibende_ects = max(verbleibende_ects, 0)
            actual_rest.append(verbleibende_ects)
            had_flags.append(len(kurse_in_monat) > 0)

            monat_display = monat.strftime("%b %Y")
            if kurse_in_monat:
                kurse_text = "<br>".join([f"• {n} ({e} ECTS)" for n, e in kurse_in_monat])
                hover_texts.append(
                    f"<b>{monat_display}</b><br><b>Abgeschlossen:</b><br>{kurse_text}<br>"
                    f"<b>Verbleiben noch {verbleibende_ects:.0f} ECTS</b>"
                )
            else:
                hover_texts.append(
                    f"<b>{monat_display}</b><br>Verbleibende ECTS: {verbleibende_ects:.0f}"
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

    def build_notenverlauf(self, student_id: int, studiengang_id: Optional[int]) -> NotenverlaufViewModel:
        try:
            daten = self.progress.notenverlauf_daten(student_id, studiengang_id)

            if not daten.noten:
                return NotenverlaufViewModel(
                    hat_daten=False,
                    fehlermeldung="Noch keine Noten vorhanden."
                )

            # UI: Kursnamen ggf. kürzen
            kursnamen_ui: List[str] = []
            for name in daten.kursnamen:
                label = name
                if len(label) > 20:
                    label = label[:17] + "..."
                kursnamen_ui.append(label)

            return NotenverlaufViewModel(
                kursnamen=kursnamen_ui,
                noten=daten.noten,
                pruefungsformen=daten.pruefungsformen,
                durchschnittsverlauf=daten.durchschnittsverlauf,
                durchschnitt=daten.aktueller_schnitt,
                beste_note=daten.beste_note,
                anzahl_kurse=len(daten.noten),
                hat_daten=True,
                fehlermeldung=None,
            )
        except Exception as e:
            return NotenverlaufViewModel(
                hat_daten=False,
                fehlermeldung=str(e)
            )

    # =====================================================================
    # 6) Bearbeitungsverlauf
    # =====================================================================

    def build_bearbeitungsverlauf(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> BearbeitungsverlaufViewModel:
        vm = BearbeitungsverlaufViewModel()
        try:
            daten = self.progress.bearbeitungsverlauf_daten(student_id, studiengang_id)

            if not daten or not daten.eintraege:
                vm.hat_daten = False
                vm.fehlermeldung = "Noch keine abgeschlossenen Bearbeitungen vorhanden."
                return vm

            for e in daten.eintraege:
                kurs_label = e.kurs_kuerzel or e.kurs_name

                vm.eintraege.append(
                    BearbeitungsverlaufEintrag(
                        kurs_label=kurs_label,
                        start_datum=e.start_datum,
                        abgabe_datum=e.abgabe_datum,
                        dauer_tage=e.dauer_tage,
                    )
                )

            if not vm.eintraege:
                vm.hat_daten = False
                vm.fehlermeldung = "Noch keine Bearbeitungen vorhanden."
                return vm

            vm.eintraege.sort(key=lambda x: (x.start_datum or date.min, x.kurs_label))

            vm.durchschnitt = daten.durchschnitt
            vm.durchschnitt_verlauf = list(daten.durchschnitt_verlauf)

            vm.hat_daten = True
            vm.fehlermeldung = None
            return vm

        except Exception as e:
            vm.hat_daten = False
            vm.fehlermeldung = str(e)
            return vm

    # =====================================================================
    # 7) Kursplan Gantt
    # =====================================================================

    def build_kursplan(
        self,
        student_id: int,
        studiengang_id: Optional[int] = None,
    ) -> KursplanViewModel:
        vm = KursplanViewModel()
        try:
            daten = self.progress.kursplan_daten(student_id, studiengang_id)

            if not daten or not daten.eintraege:
                vm.hat_daten = False
                vm.fehlermeldung = "Noch keine Daten für den Kursplan vorhanden."
                return vm

            for e in daten.eintraege:
                kursname = e.kurs_kuerzel or e.kurs_name
                kurs_label = f"{(e.semester or 0)}. Sem – {kursname}" if e.semester else kursname

                vm.eintraege.append(
                    KursplanEintrag(
                        semester=e.semester or 0,
                        kurs_label=kurs_label,
                        plan_start=e.plan_start,
                        plan_end=e.plan_end,
                        ist_start=e.ist_start,
                        ist_end=e.ist_end,
                    )
                )

            vm.semester_optionen = list(daten.semester_optionen)
            vm.min_datum = daten.min_datum
            vm.max_datum = daten.max_datum
            vm.studium_start = daten.studium_start
            vm.studium_ende = daten.studium_ende

            vm.hat_daten = True
            vm.fehlermeldung = None
            return vm

        except Exception as e:
            vm.hat_daten = False
            vm.fehlermeldung = str(e)
            return vm
