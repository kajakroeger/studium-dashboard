"""
core/__init__.py
Dieses Paket bündelt die fachliche Logik (Application/Services).
Nach außen exportieren wir den FortschrittService und seine DTOs.
"""

from .fortschritt_service import (
    FortschrittService,
    KursFortschrittDTO,
    BearbeitungFortschrittDTO,
    GesamtFortschrittDTO,
)

__all__ = [
    "FortschrittService",
    "KursFortschrittDTO",
    "BearbeitungFortschrittDTO",
    "GesamtFortschrittDTO",
]
