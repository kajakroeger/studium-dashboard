# app.py
"""
🚪RESTAURANT-EINGANG 
- öffnet das Restaurant (startet die App)
- baut die Küche zusammen (Services + ViewModelBuilder via setup)
- entscheidet, in welchem Servierstil serviert wird (UI_BACKEND / Renderer)
- startet den Service (renderer(vm_builder))

Technisch:
- Einstiegspunkt für Streamlit
- zum Starten: streamlit run app.py
- initialisiert Infrastruktur über ui.setup (ohne DB-Details im UI-Code)
- wählt das UI-Backend über get_dashboard_renderer(...)
- triggert das Rendering des Dashboards
"""

from ui.setup import build_service
from ui.ui_adapter import get_dashboard_renderer
# from ui.theme import apply_global_theme


UI_BACKEND = "streamlit"

def main() -> None:

    # Service + ViewModelBuilder initialisieren
    vm_builder = build_service("studium.db")
    
    # Renderer holen 
    renderer = get_dashboard_renderer(UI_BACKEND)

    # Dashboard rendern
    renderer(vm_builder)
    
    # theme()

if __name__ == "__main__":
    main()
