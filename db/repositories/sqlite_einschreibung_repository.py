# db/repositories/sqlite_einschreibung_repository.py
"""
SQLite-Repo für Einschreibung: legt Ziele (Notenschnitt + Ziel-Datum) ab.
'studiengang' lassen wir vorerst NULL (später über FK erweiterbar).
"""
from __future__ import annotations
from typing import Optional, Iterable
from datetime import date

from db import ConnectionProvider
from models.einschreibung import Einschreibung, StatusEinschreibung
from .einschreibung_repository import EinschreibungRepository

class SQLiteEinschreibungRepository(EinschreibungRepository):
    def __init__(self, provider: ConnectionProvider) -> None:
        self._p = provider
        self._ensure_table()

    def _ensure_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS einschreibung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            studiengang_id INTEGER,           -- optional (NULL)
            start_datum TEXT NOT NULL,        -- ISO-String
            ziel_enddatum TEXT NOT NULL,
            ziel_notenschnitt REAL NOT NULL,
            status TEXT NOT NULL
        );
        """
        with self._p.connect() as c:
            c.execute(sql)
            c.commit()

    def get_aktive_fuer_student(self, student_id: int) -> Optional[Einschreibung]:
        with self._p.connect() as c:
            row = c.execute(
                "SELECT id, student_id, studiengang_id, start_datum, ziel_enddatum, ziel_notenschnitt, status "
                "FROM einschreibung WHERE student_id=? AND status=? ORDER BY id DESC LIMIT 1",
                (student_id, StatusEinschreibung.AKTIV.value),
            ).fetchone()
        return None if row is None else self._row_to_model(row)

    def alle_fuer_student(self, student_id: int) -> Iterable[Einschreibung]:
        with self._p.connect() as c:
            rows = c.execute(
                "SELECT id, student_id, studiengang_id, start_datum, ziel_enddatum, ziel_notenschnitt, status "
                "FROM einschreibung WHERE student_id=? ORDER BY id DESC",
                (student_id,),
            ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def create(self, e: Einschreibung) -> int:
        with self._p.connect() as c:
            cur = c.execute(
                "INSERT INTO einschreibung (student_id, studiengang_id, start_datum, ziel_enddatum, ziel_notenschnitt, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    e.student.id,
                    None,  # studiengang optional
                    e.start_datum.isoformat(),
                    e.ziel_enddatum.isoformat(),
                    e.ziel_notenschnitt,
                    e.status.value,
                ),
            )
            c.commit()
            return int(cur.lastrowid)

    def update(self, e: Einschreibung) -> None:
        with self._p.connect() as c:
            c.execute(
                "UPDATE einschreibung SET studiengang_id=?, start_datum=?, ziel_enddatum=?, ziel_notenschnitt=?, status=? "
                "WHERE id=?",
                (
                    None,  # studiengang optional
                    e.start_datum.isoformat(),
                    e.ziel_enddatum.isoformat(),
                    e.ziel_notenschnitt,
                    e.status.value,
                    getattr(e, "id", None),
                ),
            )
            c.commit()

    # --- Mapping ---
    @staticmethod
    def _row_to_model(row) -> Einschreibung:
        from models.student import Student  # lazy import, um Zyklen zu vermeiden
        # wir füllen nur das Nötigste; Studiengang bleibt None
        dummy_student = Student(id=row["student_id"], name=f"Student #{row['student_id']}", matrikelnummer="n/a")
        return Einschreibung(
            student=dummy_student,
            studiengang=None,
            start_datum=date.fromisoformat(row["start_datum"]),
            ziel_enddatum=date.fromisoformat(row["ziel_enddatum"]),
            ziel_notenschnitt=row["ziel_notenschnitt"],
            status=StatusEinschreibung(row["status"]),
        )
