"""
ui/app.py
Streamlit-Einstieg: baut Service, setzt Page Config, rendert Dashboard-Seite.
Start:
    streamlit run ui/app.py
"""
import streamlit as st

from core.viewmodel_builder import ViewModelBuilder
from ui.setup import build_service
from ui.components.ui_adapter import get_dashboard_renderer
from ui.theming import apply_global_theme


UI_BACKEND = "streamlit"

def main() -> None:

    # Service + ViewModelBuilder initialisieren
    vm_builder = build_service("studium.db")
    
    # Renderer holen 
    renderer = get_dashboard_renderer(UI_BACKEND)

    # Dashboard rendern
    renderer(vm_builder)
    
    # apply_global_theme()

if __name__ == "__main__":
    main()
