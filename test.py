# def build_studienziele_status(
#         self, student_id: int, 
#         ziel_tage_pro_5ects: float = 30.0,
#         studiengang_id: Optional[int] = None
#     ) -> StudienzieleStatusViewModel:
#         """Baut das ViewModel für Studienziele-Status."""
        
#         # Aktive Einschreibung laden        
#         try:
#             einschreibung = self.service.aktive_einschreibung(student_id)
#         except Exception as e:
#             return StudienzieleStatusViewModel(
#                 hat_ziel_note=False,
#                 fehlermeldung=str(e)
#             )
        
#         if not einschreibung:
#             return StudienzieleStatusViewModel(
#                 hat_ziel_note=False,
#                 fehlermeldung="Keine aktive Einschreibung gefunden."
#             )
        
#         # Zielnote laden
#         try:
#             ziel_note = einschreibung.ziel_notenschnitt if einschreibung else None
#         except Exception as e:
#             return StudienzieleStatusViewModel(
#                 hat_ziel_note=False,
#                 fehlermeldung=str(e)
#             )
        
#         if not ziel_note:
#             return StudienzieleStatusViewModel(
#                 hat_ziel_note=False,
#                 fehlermeldung="Noch keine Ziel-Note hinterlegt."
#             )   
        
#         # Aktuellen Schnitt laden 
#         try:
#             aktueller_schnitt = self.service.berechne_notenschnitt(student_id)
#         except Exception as e:
#             return StudienzieleStatusViewModel(
#                 hat_ziel_note=False,
#                 fehlermeldung=str(e)
#             )
        
#         if not aktueller_schnitt:
#             return StudienzieleStatusViewModel(
#                 hat_ziel_note=False,
#                 fehlermeldung="Noch keine Noten vorhanden."
#             )
        
#         # Noten
#         noten = self.service.alle_bestandenen_noten(student_id)
#         gesamt_noten = sum(noten)
#         anzahl_noten = len(noten)
        
#         # Studiengang
#         studiengaenge = self.service.studiengaenge_by_student_id(student_id)
#         studiengang = studiengaenge[0] if studiengaenge else None
#         gesamt_kurse = studiengang.anzahl_kurse if studiengang else None
        
#         rest_kurse = None
#         if gesamt_kurse and anzahl_noten is not None:
#             rest_kurse = max(gesamt_kurse - anzahl_noten, 0)
        
#         # Berechnungen
#         benoetigte_note_naechster_kurs = None
#         benoetigter_durchschnitt_rest = None
#         best_moeglicher_schnitt = None
#         # ziel_erreicht = False
        
#         if ziel_note and anzahl_noten > 0:
#             required = ziel_note * (anzahl_noten + 1) - gesamt_noten
#             best_moeglicher_schnitt = (gesamt_noten + 1.0) / (anzahl_noten + 1)
            
#             if 1.0 <= required <= 5.0:
#                 benoetigte_note_naechster_kurs = round(required, 2)
            
#             if gesamt_kurse and rest_kurse and rest_kurse > 0:
#                 required_avg = (ziel_note * gesamt_kurse - gesamt_noten) / rest_kurse
#                 if required_avg <= 5.0:
#                     benoetigter_durchschnitt_rest = round(max(required_avg, 1.0), 2)
            
#             ziel_erreicht = aktueller_schnitt <= ziel_note if aktueller_schnitt else False
        
#         # Tempo
#         try:
#             ist_tage = self.service.bearbeitungszeit_durchschnitt(student_id)
#         except Exception as e:
#             ist_tage = None

#         tempo_abweichung = {
#             ist_tage - ziel_tage_pro_5ects
#             if ist_tage is not None 
#             else None
#         }

#         return StudienzieleStatusViewModel(
#             aktueller_schnitt=aktueller_schnitt,
#             ziel_note=ziel_note,
#             benoetigte_note_naechster_kurs=benoetigte_note_naechster_kurs,
#             benoetigter_durchschnitt_rest=benoetigter_durchschnitt_rest,
#             best_moeglicher_schnitt_naechster_kurs=best_moeglicher_schnitt,
#             rest_kurse=rest_kurse,
#             anzahl_noten=anzahl_noten,
#             ziel_erreicht=ziel_erreicht,
#             ist_tage_pro_5ects=ist_tage,
#             ziel_tage_pro_5ects=ziel_tage_pro_5ects,
#             tempo_abweichung=tempo_abweichung,
#             hat_ziel_note=ziel_note is not None,
#             hat_tempo_daten=ist_tage is not None,
#             fehlermeldung=None
#         )