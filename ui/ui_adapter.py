"""
Datei: ui/ui_adapter.py
Beschreibung:
Definiert die abstrakte UI-Schnittstelle. So bleibt die Fachlogik unabhängig von
konkreten UI-Technologien (Streamlit, CLI, Flask, ...).
"""

from __future__ import annotations
from abc import ABC, abstractmethod


class UIAdapter(ABC):
    """Abstrakte Schnittstelle für alle UI-Adapter."""

    @abstractmethod
    def zeige_dashboard(self) -> None:
        """
        Rendert das Dashboard der Anwendung.
        Rückgabe: None, weil die konkrete UI (z. B. Streamlit) selbst rendert.
        """
        raise NotImplementedError
