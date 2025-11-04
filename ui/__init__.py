"""
ui/__init__.py
Exportiert die UI-Schnittstelle (UIAdapter) und die Streamlit-Implementierung.
"""

from .ui_adapter import UIAdapter
from .streamlit_dashboard_ui import StreamlitDashboardUI

__all__ = ["UIAdapter", "StreamlitDashboardUI"]
