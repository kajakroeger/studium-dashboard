"""
Datei: db/connection_provider.py
Beschreibung:
Definiert die *Schnittstelle* für das Herstellen/Schließen von DB-Verbindungen.
Repositories hängen NUR von diesem Interface ab – nicht von einer konkreten DB (SQLite, Postgres, …).

Hinweise:
- get_connection() gibt ein Objekt zurück, das mindestens .execute(), .commit(), .close() anbietet.
- Die Methode connect() (Context Manager) ist optionaler Komfort: mit 'with provider.connect() as conn: …'
  ermöglicht automatische Aufräum-Logik.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Protocol, Iterator, Any


class DBConnection(Protocol):
    """
    🚪 LAGERZUGANG / TÜR
    - definiert, WIE ein Lager betreten wird (Verbindung öffnen/schließen)
    - kennt KEINE Lebensmittel, KEINE Regale, KEINE Fachlogik
    - stellt nur den Zugang bereit

    Technisch:
    - Abstraktion für Datenbank-Verbindungen
    - Repositories kennen nur dieses Interface, nicht SQLite direkt
    - erlaubt späteren Wechsel (z. B. SQLite → PostgreSQL), ohne Repositories zu ändern
    """
    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] | None = ...) -> Any: ...
    def commit(self) -> None: ...
    def close(self) -> None: ...

class ConnectionProvider(ABC):
    """
    👨‍💼🗝️ LAGERMEISTER 
    - kann Lager öffnen und schließen
    - nutzt bei Bedarf verschiedene Schlüssel
    - stellt nur den Zugang bereit

    Technisch:
    - abstraktes Interface für Datenbank-Zugriff
    - konkrete Implementierungen (SQLite, Postgres, …) regeln das WIE
      bzw. welchen Schlüssel der Lagermeister nutzt
    """

    @abstractmethod
    def get_connection(self) -> DBConnection:
        """
        Stellt eine neue DB-Verbindung her.
        Wichtig: Der Aufrufer ist für das Schließen verantwortlich – oder nutzt 'connect()'.
        """
        raise NotImplementedError

    @abstractmethod
    def close_connection(self, conn: DBConnection) -> None:
        """Schließt die übergebene Verbindung."""
        raise NotImplementedError

    # --- Komfort: Context Manager zum sicheren Öffnen/Schließen ---
    @contextmanager
    def connect(self) -> Iterator[DBConnection]:
        """
        Kontextmanager für bequemen & sicheren Verbindungsumgang mit:
            with provider.connect() as conn:
                conn.execute("INSERT ...")
                conn.commit()
        """
        # Verbindung aufbauen
        conn = self.get_connection()
        try:
            yield conn
        finally:
            # Verbindung schließen
            self.close_connection(conn)
