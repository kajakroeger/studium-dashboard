from __future__ import annotations
from typing import Protocol

from core import get_progress_service, get_workflow_service
from core.viewmodel_builder import ViewModelBuilder


class UIAdapter(Protocol):
    """
    Ein Renderer, der das Dashboard zeichnet.
    Signatur: (vm_builder) -> None
    """
    def __call__(self, vm_builder: ViewModelBuilder) -> None:
        ...


def get_dashboard_renderer(ui_backend: str) -> UIAdapter:
    """
    Gibt die passende Render-Funktion zurück.
    Lädt die Services erst bei tatsächlicher Nutzung.
    """

    if ui_backend == "streamlit":
        from ui.pages.dashboard_page_streamlit import render_dashboard_streamlit
        return render_dashboard_streamlit

    raise ValueError(f"Unbekannter UI-Backend: {ui_backend!r}")
