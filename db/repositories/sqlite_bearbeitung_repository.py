# db/repositories/sqlite_bearbeitung_repository.py
"""
SQLite-Skelett für BearbeitungRepository.
Beachtet Enum-Konvertierung für StatusBearbeitung.
Implementiert CRUD-Methoden und Tabelleninitialisierung.
"""

from __future__ import annotations
from typing import Iterable, Optional
from datetime import date

from db import ConnectionProvider
from models.bearbeitung import Bearbeitung, StatusBearbeitung
from .bearbeitung_repository import BearbeitungRepository


class SQLiteBearbeitungRepository(BearbeitungRepository):
    """Konkreter SQLite-Adapter für BearbeitungRepository."""

    def __init__(self, provider: ConnectionProvider) -> None:
        self._provider = provider
        self._ensure_table()

    # legt Datenbanktabelle an, falls sie noch nicht existiert
    def _ensure_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS bearbeitung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kurs_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            start_datum DATE NOT NULL,
            status TEXT NOT NULL,
            thema TEXT,
            abgabe_datum DATE
        );
        """
        with self._provider.connect() as conn:
            conn.execute(sql)
            conn.commit()
    
    # Public API
    def get_by_id(self, bearbeitung_id: int) -> Optional[Bearbeitung]:
        with self._provider.connect() as conn:
            row = conn.execute(
                "SELECT id, kurs_id, student_id, start_datum, status, thema, abgabe_datum "
                "FROM bearbeitung WHERE id=?",
                (bearbeitung_id,),
            ).fetchone()
        return None if row is None else self._row_to_model(row)

    def all_for_student(self, student_id: int) -> Iterable[Bearbeitung]:
        with self._provider.connect() as conn:
            rows = conn.execute(
                "SELECT id, kurs_id, student_id, start_datum, status, thema, abgabe_datum "
                "FROM bearbeitung WHERE student_id=? ORDER BY start_datum DESC",
                (student_id,),
            ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def create(self, b: Bearbeitung) -> int:
        with self._provider.connect() as conn:
            cur = conn.execute(
                "INSERT INTO bearbeitung (kurs_id, student_id, start_datum, status, thema, abgabe_datum) "
                "VALUES (?,?,?,?,?,?)",
                (
                    b.kurs_id,
                    b.student_id,
                    b.start_datum.isoformat(),
                    b.status.value,
                    b.thema,
                    b.abgabe_datum.isoformat() if b.abgabe_datum else None,
                ),
            )
            conn.commit()
            new_id = int(cur.lastrowid)  # type: ignore[arg-type]
        b.id = new_id
        return new_id

    def update(self, b: Bearbeitung) -> None:
        with self._provider.connect() as conn:
            conn.execute(
                "UPDATE bearbeitung SET kurs_id=?, student_id=?, start_datum=?, status=?, thema=?, abgabe_datum=? "
                "WHERE id=?",
                (
                    b.kurs_id,
                    b.student_id,
                    b.start_datum.isoformat(),
                    b.status.value,
                    b.thema,
                    b.abgabe_datum.isoformat() if b.abgabe_datum else None,
                    b.id,
                ),
            )
            conn.commit()

    def delete(self, bearbeitung_id: int) -> None:
        with self._provider.connect() as conn:
            conn.execute("DELETE FROM bearbeitung WHERE id=?", (bearbeitung_id,))
            conn.commit()

    # Mapping-Helfer
    @staticmethod
    def _row_to_model(row) -> Bearbeitung:
        # Datum-Parsing (ISO-Strings → date). SQLite gibt Strings zurück.
        def parse_date(val) -> Optional[date]:
            return None if val is None else date.fromisoformat(val)

        return Bearbeitung(
            id=row["id"],
            kurs_id=row["kurs_id"],
            student_id=row["student_id"],
            start_datum=parse_date(row["start_datum"]),  # type: ignore[arg-type]
            status=StatusBearbeitung(row["status"]),
            thema=row["thema"],
            abgabe_datum=parse_date(row["abgabe_datum"]),
        )
