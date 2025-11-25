# db/repositories/sqlite_studiengang_repository.py
"""
SQLite-Implementierung des StudiengangRepository.
Erstellt Tabelle idempotent und bietet get_or_create per Name.
"""
from __future__ import annotations
from typing import Optional
from db.connection_provider import ConnectionProvider
from .studiengang_repository import StudiengangRepository
from models import Studiengang

class SQLiteStudiengangRepository(StudiengangRepository):
    def __init__(self, provider: ConnectionProvider) -> None:
        self._provider = provider
        self._ensure_schema()

    def provider(self):
        return self._provider

    def _ensure_schema(self) -> None:
        with self._provider.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS studiengang (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    anzahl_monate INTEGER NOT NULL,
                    anzahl_kurse INTEGER NOT NULL,
                    ects_gesamt INTEGER NOT NULL
                );
            """)
            conn.commit()

    def create(self, s: Studiengang) -> int:
        with self._provider.connect() as conn:
            cur = conn.execute("""
                INSERT INTO studiengang (name, anzahl_monate, anzahl_kurse, ects_gesamt)
                VALUES (?, ?, ?, ?)
            """, (s.name, s.anzahl_monate, s.anzahl_kurse, s.ects_gesamt))
            conn.commit()
            new_id = int(cur.lastrowid)  # type: ignore[arg-type]
        s.id = new_id
        return new_id

    def get_by_id(self, sid: int) -> Studiengang:
        with self._provider.connect() as conn:
            row = conn.execute("SELECT * FROM studiengang WHERE id=?", (sid,)).fetchone()
        if not row:
            return None
        return Studiengang(
            id=int(row["id"]),
            name=row["name"],
            anzahl_monate=int(row["anzahl_monate"]),
            anzahl_kurse=int(row["anzahl_kurse"]),
            ects_gesamt=int(row["ects_gesamt"]),
        )
    

    def get_by_name(self, name: str) -> Studiengang:
        with self._provider.connect() as conn:
            row = conn.execute("SELECT * FROM studiengang WHERE name=?", (name,)).fetchone()
        if not row:
            return None
        return Studiengang(
            id=int(row["id"]),
            name=row["name"],
            anzahl_monate=int(row["anzahl_monate"]),
            anzahl_kurse=int(row["anzahl_kurse"]),
            ects_gesamt=int(row["ects_gesamt"]),
        )
    
    def all(self):
        with self._provider.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, anzahl_monate, anzahl_kurse, ects_gesamt FROM studiengang ORDER BY id"
            ).fetchall()
        return [self._row_to_model(r) for r in rows]
        
    @staticmethod
    def _row_to_model(row) -> Studiengang:
        """KRITISCH: ID muss korrekt gemappt werden!"""
        return Studiengang(
            id=int(row["id"]),  
            name=row["name"],
            anzahl_monate=int(row["anzahl_monate"]),
            anzahl_kurse=int(row["anzahl_kurse"]),
            ects_gesamt=int(row["ects_gesamt"]),
        )
