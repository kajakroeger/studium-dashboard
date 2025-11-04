"""
Datei: db/sqlite_connection_provider.py
Beschreibung:
Konkreter ConnectionProvider für SQLite.
- Kümmert sich um Aufbau/Schließen der Verbindung
- Aktiviert sinnvolle Defaults (Row-Factory, Foreign Keys)
- Bleibt kompatibel zum abstrakten Interface (ConnectionProvider)

Verwendung (Beispiel):
    provider = SQLiteConnectionProvider("studium.db")
    with provider.connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS student (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
"""

from __future__ import annotations

import sqlite3
from typing import Any, Mapping, Optional

from .connection_provider import ConnectionProvider, DBConnection


class SQLiteConnectionProvider(ConnectionProvider):
    """
    Stellt SQLite-Verbindungen bereit.
    Die Repositories erhalten diesen Provider injiziert, kennen aber nur das Interface.
    """

    def __init__(self, db_path: str, *, pragmas: Optional[Mapping[str, Any]] = None) -> None:
        """
        Args:
            db_path: Pfad zur SQLite-Datei (z. B. 'studium.db')
            pragmas: optionale PRAGMA-Einstellungen, z. B. {"foreign_keys": 1}
                     Standard: foreign_keys=ON
        """
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
        # Optional: Typ-Erkennung aktivieren (falls DATE-Konverter genutzt wird)
        # conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

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
