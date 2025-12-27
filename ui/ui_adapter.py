from __future__ import annotations
from typing import Protocol

from core.viewmodel_builder import ViewModelBuilder

class UIAdapter(Protocol):
    """
    ❇️ SERVIERSTIL
    - legt den Stil des Restaurants fest bzw. wie die Gerichte präsentiert werden
      z.B. Essen im Dunkeln (CLI, keine visuelle Darstellung), Streamlit (offene Showküche, da direkte Rückmeldung)

    Technisch:
    - beschreibt, wie ein UI-Backend das Dashboard rendert
    - nimmt einen ViewModelBuilder (Anrichter) entgegen
    - das UI-Backend bleibt damit leicht austauschbar
    """
    def __call__(self, vm_builder: ViewModelBuilder) -> None:
        ...


def get_dashboard_renderer(ui_backend: str) -> UIAdapter:
    """
    ❇️ SERVIERSTIL-AUSWAHL 
    - wählt die konkrete Präsentationsform (UI-Backend)
    - aktuell Sreamlit
    - möglich Alternativen: CLI, Web, Mobile, Export (PDF)

    Technisch:
    - gibt eine Render-Funktion zurück, die dem UIAdapter-Protocol entspricht
    - nutzt Lazy Imports: das konkrete Backend-Modul wird erst importiert,
      wenn es wirklich ausgewählt wurde (entkoppelt Backends)
    """

    if ui_backend == "streamlit":
        from ui.streamlit.pages.dashboard_page_streamlit import render_dashboard_streamlit
        return render_dashboard_streamlit

    raise ValueError(f"Unbekannter UI-Backend: {ui_backend!r}")
