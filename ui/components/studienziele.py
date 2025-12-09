# ui/components/studienziele.py
"""
Zeigt die Studienziele (Ziel-Abschlussdatum, Ziel-Notenschnitt) an.
"""
import streamlit as st

from core.view_models import StudienzieleViewModel
from .kachel import kachel


def render_studienziele(vm: StudienzieleViewModel):
    """
    Zeigt die Studienziele aus der aktiven Einschreibung an.
    """
    with kachel("STUDIENZIELE"):
        # Aktive Einschreibung holen

        if not vm.hat_einschreibung:
            st.info(vm.fehlermeldung)
            return
        
        if vm.ziel_enddatum_str:
            st.write(f"Ziel Abschlussdatum: {vm.ziel_enddatum_str}")
        else:
            st.write(vm.fehlermeldung)
        if vm.ziel_notenschnitt:
            st.write(f"Ziel Notenschnitt: {vm.ziel_notenschnitt:.2f}")
        else:
            st.write(vm.fehlermeldung)

