# db/__init__.py
"""
- enthält alle Module rund um den Datenbankzugriff
- Beinhaltet:
    - DBConnection
    - ConnectionProvider-Interface
    - SQLiteConnectionProvider-Implementierung
"""

from .connection_provider import DBConnection, ConnectionProvider 
from .sqlite_connection_provider import SQLiteConnectionProvider

__all__ = [
    "DBConnection",             # 🚪 LAGERZUGANG / TÜR
    "ConnectionProvider",       # 👨‍💼 TÜRSTEHER 
    "SQLiteConnectionProvider", # 🗝️ LAGERSCHLÜSSEL (SQLite)
]
