# db/repositories/sqlite_kurs_repository.py
"""
SQLite-Implementierung des KursRepository.
- Nutzt ConnectionProvider (bleibt dadurch DB-agnostisch auf Interface-Ebene)
- Verwendet sqlite3.Row (dict-ähnlicher Zugriff)
- Enthält Mapping-Funktionen DB <-> Model
"""

from __future__ import annotations
import sqlite3
from typing import Iterable, Optional

from db import ConnectionProvider
from models.kurs import Kurs
from .kurs_repository import KursRepository


class SQLiteKursRepository(KursRepository):
    """Konkreter SQLite-Adapter für KursRepository."""
    def __init__(self, provider: ConnectionProvider) -> None:
        self._provider = provider
        self.provider = provider
        self._ensure_table()

    # Datenbanktabelle anlegen, falls sie noch nicht existiert 
    def _ensure_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS kurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kurs_kuerzel TEXT NOT NULL,
            ects INTEGER NOT NULL,
            tutor TEXT,
            semester_nummer INTEGER
        );
        """
        with self._provider.connect() as conn:
            conn.execute(sql)
            # Duplikate verhindern: Name und Kürzel dürfen beide einzeln nicht doppelt vorkommen
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_kurs_name ON kurs(name);")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_kurs_kuerzel ON kurs(kurs_kuerzel);")

    # Public API 
    def get_by_id(self, kurs_id: int) -> Optional[Kurs]:
        with self._provider.connect() as conn:
            row = conn.execute(
                "SELECT id, name, kurs_kuerzel, ects, tutor, semester_nummer FROM kurs WHERE id=?",
                (kurs_id,),
            ).fetchone()
        return None if row is None else self._row_to_model(row)

    def all(self) -> Iterable[Kurs]:
        with self._provider.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, kurs_kuerzel, ects, tutor, semester_nummer FROM kurs ORDER BY name"
            ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def create(self, kurs: Kurs) -> int:
        try:    
            with self._provider.connect() as conn:
                cur = conn.execute(
                    "INSERT INTO kurs (name, kurs_kuerzel, ects, tutor, semester_nummer) VALUES (?,?,?,?,?)",
                    (kurs.name, kurs.kurs_kuerzel, kurs.ects, getattr(kurs, "tutor", None), getattr(kurs.semester, "nummer", None)),
                )
                conn.commit()
                new_id = int(cur.lastrowid)  # type: ignore[arg-type]
            setattr(kurs, "id", new_id)
            return new_id
        except sqlite3.IntegrityError as e:
            raise ValueError("Kurs mit diesem Namen oder Kürzel existiert bereits.") from e

    def update(self, kurs: Kurs) -> None:
        with self._provider.connect() as conn:
            conn.execute(
                "UPDATE kurs SET name=?, kurs_kuerzel=?, ects=?, tutor=?, semester_nummer=? WHERE id=?",
                (kurs.name, kurs.kurs_kuerzel, kurs.ects, getattr(kurs, "tutor", None), getattr(kurs.semester, "nummer", None), getattr(kurs, "id", None)),
            )
            conn.commit()

    def delete(self, kurs_id: int) -> None:
        with self._provider.connect() as conn:
            conn.execute("DELETE FROM kurs WHERE id=?", (kurs_id,))
            conn.commit()


    # ----- Existenzprüfungen -----
    def exists_by_name(self, name: str) -> bool:
        sql = "SELECT 1 FROM kurs WHERE LOWER(name) = LOWER(?) COLLATE NOCASE LIMIT 1;"
        with self.provider.get_connection() as conn:
            return conn.execute(sql, (name,)).fetchone() is not None
    
    def exists_by_kuerzel(self, kurs_kuerzel: str) -> bool:
        sql = "SELECT 1 FROM kurs WHERE LOWER(kurs_kuerzel) = LOWER(?) COLLATE NOCASE LIMIT 1;"
        with self.provider.get_connection() as conn:
            return conn.execute(sql, (kurs_kuerzel,)).fetchone() is not None


    # Mapping-Helfer
    @staticmethod
    def _row_to_model(row) -> Kurs:
        """Konvertiert eine sqlite3.Row in ein Kurs-Objekt."""
        return Kurs(
            name=row["name"],
            kurs_kuerzel=row["kurs_kuerzel"],
            ects=row["ects"],
            tutor=row["tutor"],
            semester=None,  # Falls du Semester-Objekte laden willst, später via SemesterRepo verknüpfen
        )
