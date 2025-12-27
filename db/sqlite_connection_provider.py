from __future__ import annotations

import sqlite3
from typing import Any, Mapping, Optional

from db import *


class SQLiteConnectionProvider(ConnectionProvider):
    """
    🗝️ LAGERSCHLÜSSEL (SQLite)
    - öffnet und schließt den Zugang zum Lager (SQLite-Datei) mittels sqlite3-Schlüssel  
    - stellt sicher, dass Verbindungen korrekt erzeugt werden

    Technisch:
    - konkrete Implementierung des ConnectionProvider
    - kapselt sqlite3.connect(...)
    - kümmert sich um:
        - Connection-Lebenszyklus
        - Row-Factory (dict-ähnlicher Zugriff)
        - Pfad zur DB-Datei
    """

    def __init__(self, db_path: str, *, pragmas: Optional[Mapping[str, Any]] = None) -> None:
        self.db_path = db_path
        self._pragmas: dict[str, Any] = {"foreign_keys": 1}
        if pragmas:
            self._pragmas.update(pragmas)

    def get_connection(self) -> DBConnection:
        """
        Öffnet eine neue Verbindung.
        - row_factory = sqlite3.Row (ergibt dict-ähnliche Zeilen)
        - setzt gewünschte PRAGMAs (z. B. Foreign Keys)
        """
        conn = sqlite3.connect(self.db_path)

        # Zeilen als sqlite3.Row zurückgeben (bequemer in Repos)
        conn.row_factory = sqlite3.Row  # type: ignore[attr-defined]

        # Sinnvolle PRAGMAs setzen
        for key, value in self._pragmas.items():
            conn.execute(f"PRAGMA {key} = {value}")

        return conn  # passt zum DBConnection-Protocol


    def close_connection(self, conn: DBConnection) -> None:
        """Schließt die Verbindung zuverlässig."""
        try:
            conn.close()
        except Exception:
            # Im Fehlerfall kein Re-Raise – Schließen sollte „best effort“ sein.
            pass
