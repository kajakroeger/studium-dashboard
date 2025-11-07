"""
ui/theming.py
Zentrale Definition von Farben, Schriftarten, Abständen und UI-Helfern.
Sorgt für ein konsistentes Aussehen im gesamten Dashboard.
"""

import streamlit as st
from typing import Optional

# 🎨 Farben (Farbschema des Dashboards)
PRIMARY_COLOR = "#2563EB"  
SECONDARY_COLOR = "#1E293B"  
ACCENT_COLOR = "#16A34A"        # Grün für positive Werte
DANGER_COLOR = "#DC2626"        # Rot für Fehler/negative Werte
BACKGROUND_COLOR = "#087CF8"
TEXT_COLOR = "#132E6E"

# 🖋️ Typografie
FONT_FAMILY = "Inter, sans-serif"
TITLE_SIZE = "28px"
SUBTITLE_SIZE = "18px"
TEXT_SIZE = "15px"

# 🧱 Abstände
PADDING_SMALL = "0.5rem"
PADDING_MEDIUM = "1rem"
PADDING_LARGE = "2rem"

# ✅ Formatierungshelfer
def fmt_bool(value: Optional[bool]) -> str:
    if value is None:
        return "—"
    return "✅" if value else "❌"

# 🧠 Theme-initialisierung (optional)
def apply_global_theme() -> None:
    """
    Setzt globale CSS-Stile für Streamlit (z. B. Schriftart, Farben).
    Wird am besten am Anfang der App aufgerufen.
    """
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: {FONT_FAMILY};
            color: {TEXT_COLOR};
            background-color: {BACKGROUND_COLOR};
        }}
        h1, h2, h3, h4 {{
            color: {PRIMARY_COLOR};
        }}
        .stMetric {{
            background: white;
            border-radius: 12px;
            padding: {PADDING_SMALL};
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
