"""
ui/app.py
Streamlit-Einstieg: baut Service, setzt Page Config, rendert Dashboard-Seite.
Start:
    streamlit run ui/app.py
"""
import streamlit as st
from ui.setup import build_service
from ui.pages.dashboard_page import render_dashboard
from ui.theming import apply_global_theme


def main() -> None:
    st.set_page_config(page_title="Studium Dashboard", page_icon="🎓", layout="wide")
    service = build_service("studium.db")
    render_dashboard(service)    

    # apply_global_theme()

if __name__ == "__main__":
    main()
