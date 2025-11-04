"""
db/__init__.py
Dieses Paket enthält alle Module rund um den Datenbankzugriff.
Beinhaltet:
- ConnectionProvider-Interface
- SQLiteConnectionProvider-Implementierung
- Alle Repository-Interfaces und deren SQLite-Implementierungen
"""

from .connection_provider import ConnectionProvider
from .sqlite_connection_provider import SQLiteConnectionProvider

# explizit exportieren, was öffentlich ist
__all__ = [
    "ConnectionProvider",
    "SQLiteConnectionProvider",
]
