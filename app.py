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
    # Backend bauen (DB, Repos, Service)
    service = build_service("studium.db")

    # ViewModel-Builder initialisieren
    vm_builder = ViewModelBuilder(service)

    # Renderer holen 
    renderer = get_dashboard_renderer(UI_BACKEND)
    
    # Dashboard rendern
    renderer(service, vm_builder)
    
    # apply_global_theme()

if __name__ == "__main__":
    main()
