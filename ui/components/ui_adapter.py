# ui/adapters.py
"""UI-Adapter: Liefert je nach UI_BACKEND die passende Dashboard-Render-Funktion."""

from __future__ import annotations
from typing import Protocol, Callable
from core import FortschrittService
from core.viewmodel_builder import ViewModelBuilder


class UIAdapter(Protocol):
    """
    Ein Renderer, der das Dashboard zeichnet.
    Signatur: (service, vm_builder) -> None
    """
    def __call__(
        self,
        service: FortschrittService,
        vm_builder: ViewModelBuilder,
    ) -> None:  # pragma: no cover
        ...


def get_dashboard_renderer(ui_backend: str) -> UIAdapter:
    """Gibt die passende Render-Funktion für das Dashboard zurück."""
    
    if ui_backend == "streamlit":
        # Import hier, damit Streamlit nur benutzt wird, wenn dieser Pfad aktiv ist
        from ui.pages.dashboard_page_streamlit import render_dashboard_streamlit
        return render_dashboard_streamlit

    # Alternative UIs, z.B. CLI:
    # if ui_backend == "cli":
    #     from ui.cli.dashboard_page_cli import render_dashboard_cli
    #     return render_dashboard_cli

    raise ValueError(f"Unbekannter UI-Backend: {ui_backend!r}")
