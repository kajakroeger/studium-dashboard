from __future__ import annotations
from typing import Optional, List
import streamlit as st
from .kachel import kachel

def render_studienziele_status(service, student_id: int, ziel_tage_pro_5ects: float = 30.0):
    """
    Zeigt den aktuellen Status der Ziele an:
    - aktueller Notenschnitt + benötigte nächste Note + benötigter Schnitt in den restlichen Kursen
    - durchschnittliche Bearbeitungszeit pro 5 ECTS + Abweichung zum Ziel
    - offene ECTS
    """
    with kachel("AKTUELLER STATUS DER ZIELE"):

        # ---------- Gemeinsame Basisdaten ----------

        # Aktueller Notenschnitt (nur bestandene Prüfungen)
        try:
            aktueller_schnitt = service.berechne_notenschnitt(student_id)
        except Exception:
            aktueller_schnitt = None

        # Aktive Einschreibung + Zielnote
        try:
            eins = getattr(service, "aktive_einschreibung", lambda _sid: None)(student_id)
        except Exception:
            eins = None

        ziel_note: Optional[float] = getattr(eins, "ziel_notenschnitt", None)

        # Studiengang (für anzahl_kurse & ects_gesamt)
        try:
            studiengaenge = service.studiengaenge_by_student_id(student_id) or []
        except Exception:
            studiengaenge = []

        sg = studiengaenge[0] if studiengaenge else None
        gesamt_kurse: Optional[int] = getattr(sg, "anzahl_kurse", None)

        # Alle bisherigen Noten (nur bestandene)
        try:
            noten: list[float] = service.alle_bestandenen_noten(student_id) or []
        except Exception:
            noten = []

        gesamt_noten = sum(noten)
        anzahl_noten = len(noten)

        # Restliche Kurse (basierend auf anzahl_kurse im Studiengang)
        rest_kurse: Optional[int] = None
        if gesamt_kurse is not None and anzahl_noten is not None:
            rest_kurse = max(gesamt_kurse - anzahl_noten, 0)

        # ---------- 1) Noten-Ziel: benötigte Note & benötigter Durchschnitt ----------

        benoetigte_note_naechster_kurs: Optional[float] = None
        benoetigter_avg_rest: Optional[float] = None
        best_moeglicher_schnitt_naechster_kurs: Optional[float] = None

        if ziel_note is not None and anzahl_noten > 0:
            # a) Benötigte Note im nächsten Kurs (falls mit EINEM Kurs machbar)
            # Gleichung: (gesamt_noten + required) / (anzahl_noten + 1) = ziel_note
            required = ziel_note * (anzahl_noten + 1) - gesamt_noten

            # Bester möglicher Schnitt nach einem Kurs (wenn du eine 1.0 schreibst)
            best_moeglicher_schnitt_naechster_kurs = (gesamt_noten + 1.0) / (anzahl_noten + 1)

            # Gültige Note zur direkten Zielerreichung gibt es nur, wenn required in [1, 5] liegt
            if 1.0 <= required <= 5.0:
                benoetigte_note_naechster_kurs = round(required, 2)
            else:
                benoetigte_note_naechster_kurs = None  # mit EINEM Kurs nicht erreichbar

            # b) Benötigter Durchschnitt in den RESTLICHEN Kursen
            if gesamt_kurse is not None and rest_kurse is not None and rest_kurse > 0:
                # Gleichung:
                # (gesamt_noten + rest_kurse * required_avg) / gesamt_kurse = ziel_note
                required_avg = (ziel_note * gesamt_kurse - gesamt_noten) / rest_kurse

                # Wenn der notwendige Schnitt > 5.0 ist → rechnerisch nicht erreichbar
                if required_avg > 5.0:
                    benoetigter_avg_rest = None
                else:
                    # Falls du theoretisch besser als 1.0 sein müsstest, deckeln wir bei 1.0
                    if required_avg < 1.0:
                        required_avg = 1.0
                    benoetigter_avg_rest = round(required_avg, 2)

        # ---------- Layout-Spalten ----------

        c1, c2 = st.columns(2, gap="medium")

        # ---------- 1) Noten-Ziel (linke Spalte) ----------

        with c1:
            if aktueller_schnitt is None:
                st.write("Aktueller Notenschnitt", "–")
                st.caption("Noch keine bestandenen Prüfungen.")
            else:
                st.write("Aktueller Notenschnitt:", f"{aktueller_schnitt:.2f}")

                if ziel_note is None:
                    st.caption("Kein Ziel-Notenschnitt hinterlegt.")
                else:
                    # Fall A: Ziel bereits erreicht oder besser
                    if aktueller_schnitt <= ziel_note:
                        text = f"✅ Du liegst bei deiner Zielnote (Ziel: {ziel_note:.2f})."
                        if benoetigter_avg_rest is not None and rest_kurse:
                            text += (
                                f" In den verbleibenden {rest_kurse} Kursen "
                                f"solltest du im Schnitt etwa {benoetigter_avg_rest:.2f} "
                                "halten, um deine Zielnote nicht zu verlieren."
                            )
                        st.caption(text)

                    # Fall B: Ziel noch nicht erreicht
                    else:
                        text = f"ℹ️ Deine Zielnote ist {ziel_note:.2f}. "

                        # Info zum nächsten Kurs (nur wenn realistisch berechenbar)
                        if benoetigte_note_naechster_kurs is not None:
                            text += (
                                "Um sie bereits nach dem nächsten Kurs zu erreichen, "
                                f"bräuchtest du etwa eine Note von "
                                f"{benoetigte_note_naechster_kurs:.2f} oder besser. "
                            )
                        else:
                            # Hier kannst du den bestmöglichen Schnitt erwähnen
                            if best_moeglicher_schnitt_naechster_kurs is not None:
                                text += (
                                    "Mit nur einem weiteren Kurs ist sie rechnerisch "
                                    "nicht erreichbar. Selbst mit einer 1,0 im nächsten Kurs "
                                    f"würdest du nur auf etwa {best_moeglicher_schnitt_naechster_kurs:.2f} kommen. "
                                )
                            else:
                                text += (
                                    "Mit nur einem weiteren Kurs ist sie rechnerisch nicht erreichbar. "
                                )

                        # Info zum Durchschnitt in allen restlichen Kursen
                        if benoetigter_avg_rest is not None and rest_kurse:
                            text += (
                                f"In den verbleibenden {rest_kurse} Kursen "
                                f"müsstest du im Schnitt etwa {benoetigter_avg_rest:.2f} erreichen, "
                                "um deine Zielnote noch zu schaffen."
                            )

                        st.caption(text)

        # ---------- 2) Tempo & offene ECTS (rechte Spalte) ----------

        with c2:
            # Ø Bearbeitungszeit pro 5 ECTS
            try:
                ist_tage_pro_5ects = service.berechne_bearbeitungszeit(student_id)
            except Exception:
                ist_tage_pro_5ects = None


            if ist_tage_pro_5ects is None:
                st.write("Ø Bearbeitungszeit pro 5 ECTS:", "–")
                st.caption("Noch zu wenige abgeschlossene Kurse für eine Auswertung.")
            else:
                st.write(
                    "Ø Bearbeitungszeit pro 5 ECTS:",
                    f"{ist_tage_pro_5ects:.1f} Tage",
                )

                diff = ist_tage_pro_5ects - ziel_tage_pro_5ects
                if diff < -0.5:
                    st.caption(
                        f"✅ Du bist etwa {abs(diff):.1f} Tage schneller als dein Ziel "
                        f"({ziel_tage_pro_5ects:.0f} Tage pro 5 ECTS)."
                    )
                elif diff > 0.5:
                    st.caption(
                        f"⚠️ Du liegst etwa {diff:.1f} Tage über deinem Ziel "
                        f"({ziel_tage_pro_5ects:.0f} Tage pro 5 ECTS)."
                    )
                else:
                    st.caption(
                        f"👌 Du liegst ziemlich genau in deinem Zieltempo "
                        f"({ziel_tage_pro_5ects:.0f} Tage pro 5 ECTS)."
                    )