# ui/components/kachel.py
import streamlit as st
from contextlib import contextmanager

@contextmanager
def kachel(title: str):
    """Einheitlicher Kachel-Rahmen mit Überschrift."""
    with st.container(border=True):
        st.markdown(f"### {title}")
        yield
