"""
ui/__init__.py
Exportiert die UI-Schnittstelle (UIAdapter) und die Funktion zum Laden des Renderers.
"""

from .components.ui_adapter import UIAdapter

__all__ = ["UIAdapter", "get_dashboard_renderer"]
