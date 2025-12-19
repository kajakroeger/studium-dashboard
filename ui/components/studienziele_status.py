from __future__ import annotations
import streamlit as st

from core.view_models import StudienzieleStatusViewModel
from .kachel import kachel

def render_studienziele_status(view_model: StudienzieleStatusViewModel):
    """
    🥗💁‍♂️ DEKORATEUR 
    - nimmt den fertigen Teller entgegen (ViewModel)
    - serviert ihn optisch ansprechend (Layout + Visualisierung)
    - visualisiert den aktuellen Status bzgl. der Studienziele

    Technisch:
    - arbeitet ausschließlich mit ViewModels (keine DTOs, keine Models)
    - enthält keine Service-Aufrufe (kein WorkflowService/ProgressService)
    - enthält keine Geschäftslogik (keine ECTS-/Noten-Berechnungen)
    - stellt dar:
        - Streamlit-Widgets
        - Plotly-Figure bauen
        - Styling, Achsen, Hover, Leerezustände anzeigen
    """
    with kachel("AKTUELLER STATUS DER ZIELE"):
        
        # Layout: 2 Spalten
        c1, c2 = st.columns(2, gap="medium")
        
        # ==================== Linke Spalte: Noten-Ziel ====================
        with c1:
            _render_notenziel(view_model)
        
        # ==================== Rechte Spalte: Tempo ====================
        with c2:
            _render_tempo(view_model)



def _render_notenziel(vm: StudienzieleStatusViewModel):
    """Rendert die Noten-Ziel-Sektion."""

    # Kein aktueller Schnitt
    if vm.aktueller_schnitt is None:
        st.write("**Aktueller Notenschnitt:** —")
        st.caption("Noch keine bestandenen Prüfungen.")
        return

    # Aktueller Schnitt vorhanden
    st.write(f"**Aktueller Notenschnitt:** {vm.aktueller_schnitt:.2f}")

    # Keine Zielnote
    if not vm.hat_ziel_note or vm.ziel_note is None:
        st.caption("Kein Ziel-Notenschnitt hinterlegt.")
        return

    # Ziel erreicht
    if vm.ziel_erreicht:
        text = f"✅ Du liegst bei deiner Zielnote (Ziel: {vm.ziel_note:.2f})."

        if vm.benoetigter_durchschnitt_rest is not None and vm.rest_kurse:
            text += (
                f" In den verbleibenden {vm.rest_kurse} Kursen "
                f"solltest du im Schnitt etwa {vm.benoetigter_durchschnitt_rest:.1f} "
                "halten, um deine Zielnote nicht zu verlieren."
            )

        st.caption(text)
        return

    # Ziel noch nicht erreicht
    text = f"ℹ️ Deine Zielnote ist {vm.ziel_note:.2f}. "

    # Nächster Kurs – direkte Zielnote noch erreichbar?
    if vm.benoetigte_note_naechster_kurs is not None:
        text += (
            "Um deine Zielnote bereits nach dem nächsten Kurs zu erreichen, "
            f"bräuchtest du etwa eine Note von {vm.benoetigte_note_naechster_kurs:.1f} "
            "oder besser. "
        )
    else:
        # Nicht mit einem Kurs erreichbar
        if vm.best_moeglicher_schnitt_naechster_kurs is not None:
            text += (
                "Mit nur einem weiteren Kurs ist deine Zielnote rechnerisch "
                "nicht erreichbar. Mit einer 1,0 im nächsten Kurs "
                f"würdest du auf etwa {vm.best_moeglicher_schnitt_naechster_kurs:.2f} kommen. "
            )
        else:
            text += (
                "Mit nur einem weiteren Kurs ist sie rechnerisch nicht erreichbar. "
            )

    # Restliche Kurse
    if vm.benoetigter_durchschnitt_rest is not None and vm.rest_kurse:
        text += (
            f"In den verbleibenden {vm.rest_kurse} Kursen "
            f"müsstest du im Schnitt etwa {vm.benoetigter_durchschnitt_rest:.1f} erreichen, "
            "um deine Zielnote noch zu schaffen. "
        )

    if vm.note_fuer_minimale_verbesserung is not None:
        text += (
            f" Um deinen Schnitt von {vm.aktueller_schnitt:.2f} zu verbessern, "
            f"bräuchtest du mindestens eine {vm.note_fuer_minimale_verbesserung:.1f} im nächsten Kurs."
        )
    else:
        text += (
            f" Selbst mit einer 1,0 könntest du deinen Schnitt von "
            f"{vm.aktueller_schnitt:.2f} im nächsten Kurs nicht weiter verbessern."
        )

    st.caption(text)


def _render_tempo(vm: StudienzieleStatusViewModel):
    """Rendert die Tempo-Sektion (rechte Spalte)."""

    # 1) Ø Bearbeitungszeit
    if vm.ist_tage_pro_5ects is None:
        st.write("Ø Bearbeitungszeit pro 5 ECTS:", "–")
        st.caption("Noch zu wenige abgeschlossene Kurse für eine Auswertung.")
        return

    st.write(
        "Ø Bearbeitungszeit pro 5 ECTS:",
        f"{vm.ist_tage_pro_5ects:.1f} Tage",
    )

    # 2) Prognose bezüglich Ziel-Enddatum
    if vm.prognose_enddatum is None or vm.diff_tage_zum_ziel is None:
        st.caption(
            "Es liegen noch nicht genug Daten vor, um eine zuverlässige "
            "Abschluss-Prognose im Vergleich zu deinem Ziel abzugeben."
        )
        return

    prognose_str = vm.prognose_enddatum.strftime("%d.%m.%Y")
    diff = vm.diff_tage_zum_ziel

    if diff < 0:
        st.caption(
            f"✅ Wenn du in diesem Tempo weiter machst, wirst du voraussichtlich "
            f"am {prognose_str} fertig – das ist etwa {abs(diff)} Tage vor deinem Zielabschlussdatum."
        )
    elif diff > 0:
        st.caption(
            f"⚠️ In deinem aktuellen Tempo erreichst du deinen Abschluss voraussichtlich "
            f"am {prognose_str}. Das liegt etwa {diff} Tage nach deinem Zielabschlussdatum."
        )
    else:
        st.caption(
            f"👌 In deinem aktuellen Tempo liegst du ziemlich genau auf deinem "
            f"Zielabschlussdatum ({prognose_str})."
        )