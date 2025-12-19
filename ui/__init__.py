"""
💁‍♂️ℹ️ UI-REZEPTION
- stellt die öffentliche Schnittstelle der UI-Schicht bereit
- kapselt interne Implementierungsdetails (components, pages)
- erlaubt anderen Modulen, die UI zu nutzen,
  ohne ihre interne Struktur zu kennen
"""

from .components.ui_adapter import UIAdapter, get_dashboard_renderer

__all__ = [
    "UIAdapter",
    "get_dashboard_renderer",
]
