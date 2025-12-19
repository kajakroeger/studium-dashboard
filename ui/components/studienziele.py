# ui/components/studienziele.py
"""
Zeigt die Studienziele (Ziel-Abschlussdatum, Ziel-Notenschnitt) an.
"""
import streamlit as st

from core.view_models import StudienzieleViewModel
from .kachel import kachel


def render_studienziele(vm: StudienzieleViewModel):
    """
    🥗💁‍♂️ DEKORATEUR 
    - nimmt den fertigen Teller entgegen (ViewModel)
    - serviert ihn optisch ansprechend (Layout + Visualisierung)
    - visualisiert die vom Studierenden gesetzten Studienziele

    Technisch:
    - arbeitet ausschließlich mit ViewModels (keine DTOs, keine Models)
    - enthält keine Service-Aufrufe (kein WorkflowService/ProgressService)
    - enthält keine Geschäftslogik (keine ECTS-/Noten-Berechnungen)
    - stellt dar:
        - Streamlit-Widgets
        - Plotly-Figure bauen
        - Styling, Achsen, Hover, Leerezustände anzeigen
    """
    with kachel("STUDIENZIELE"):
        if not vm.hat_einschreibung:
            st.info("Noch keine aktive Einschreibung vorhanden.")
        else:
            # Ziel-Enddatum
            if vm.ziel_enddatum is not None:
                st.write(f"Ziel Abschlussdatum: {vm.ziel_enddatum}")
            else:
                st.info("Ziel Abschlussdatum: Noch nicht festgelegt.")

            # Ziel-Notenschnitt
            if vm.ziel_notenschnitt is not None:
                st.write(f"Ziel-Notenschnitt: {vm.ziel_notenschnitt:.2f}")
            else:
                st.info("Ziel-Notenschnitt: Noch nicht festgelegt.")



