"""
db/repositories/sqlite_einschreibung_repository.py
SQLite-Repo für Einschreibung: legt Schema an (idempotent) und bietet Basis-CRUD.
"""

from __future__ import annotations
from datetime import date
from typing import Iterable, Optional

from db.connection_provider import ConnectionProvider
from db.repositories.einschreibung_repository import EinschreibungRepository
from models.einschreibung import Einschreibung, StatusEinschreibung


class SQLiteEinschreibungRepository(EinschreibungRepository):
    def __init__(self, provider: ConnectionProvider) -> None:
        self._provider = provider
        self._ensure_schema()

    # ------------------------------------------------------------
    # Schema / Migration
    # ------------------------------------------------------------
    def _ensure_schema(self) -> None:
        """Erstellt die Tabelle, falls sie fehlt, und migriert fehlende Spalten."""
        with self._provider.connect() as conn:
            # Basistabelle (ohne plan_start/plan_end – die gehören zur Bearbeitung!)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS einschreibung (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    start_datum TEXT NOT NULL,
                    ziel_enddatum TEXT NOT NULL,
                    ziel_notenschnitt REAL NOT NULL,
                    status TEXT NOT NULL,
                    studiengang_id INTEGER
                )
                """
            )

            # Spalten prüfen (idempotente Migrationen)
            cols = {row["name"] for row in conn.execute("PRAGMA table_info(einschreibung)")}

            if "start_datum" not in cols:
                conn.execute("ALTER TABLE einschreibung ADD COLUMN start_datum TEXT;")
            if "ziel_enddatum" not in cols:
                conn.execute("ALTER TABLE einschreibung ADD COLUMN ziel_enddatum TEXT;")
            if "ziel_notenschnitt" not in cols:
                conn.execute("ALTER TABLE einschreibung ADD COLUMN ziel_notenschnitt REAL;")
            if "status" not in cols:
                conn.execute("ALTER TABLE einschreibung ADD COLUMN status TEXT;")
            if "studiengang_id" not in cols:
                conn.execute("ALTER TABLE einschreibung ADD COLUMN studiengang_id INTEGER;")

            conn.commit()

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    @staticmethod
    def _to_str(d: Optional[date]) -> Optional[str]:
        return d.isoformat() if d else None

    @staticmethod
    def _from_str(s: Optional[str]) -> Optional[date]:
        return date.fromisoformat(s) if s else None

    @staticmethod
    def _row_to_model(row) -> Einschreibung:
        """Mappt sqlite3.Row -> Einschreibung."""
        return Einschreibung(
            id=int(row["id"]),
            student_id=int(row["student_id"]),
            start_datum=date.fromisoformat(row["start_datum"]),
            ziel_enddatum=date.fromisoformat(row["ziel_enddatum"]),
            ziel_notenschnitt=float(row["ziel_notenschnitt"]),
            status=StatusEinschreibung(row["status"]),
            studiengang_id=(int(row["studiengang_id"]) if row["studiengang_id"] is not None else None),
        )

    # ------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------
    def create(self, eins: Einschreibung) -> int:
        """Legt eine Einschreibung an und gibt die neue ID zurück."""
        with self._provider.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO einschreibung
                    (student_id, start_datum, ziel_enddatum, ziel_notenschnitt, status, studiengang_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    eins.student_id,
                    self._to_str(eins.start_datum),
                    self._to_str(eins.ziel_enddatum),
                    float(eins.ziel_notenschnitt),
                    eins.status.value,
                    eins.studiengang_id,
                ),
            )
            conn.commit()
            new_id = int(cur.lastrowid)  # type: ignore[arg-type]
        eins.id = new_id
        return new_id

    def update(self, eins: Einschreibung) -> None:
        if eins.id is None:
            raise ValueError("Einschreibung.update: id fehlt.")
        with self._provider.connect() as conn:
            conn.execute(
                """
                UPDATE einschreibung
                SET start_datum=?, ziel_enddatum=?, ziel_notenschnitt=?, status=?, studiengang_id=?
                WHERE id=?
                """,
                (
                    self._to_str(eins.start_datum),
                    self._to_str(eins.ziel_enddatum),
                    float(eins.ziel_notenschnitt),
                    eins.status.value,
                    eins.studiengang_id,
                    eins.id,
                ),
            )
            conn.commit()

    def get_aktive_fuer_student(self, student_id: int) -> Optional[Einschreibung]:
        """Liefert die aktive Einschreibung eines Studenten (falls vorhanden)."""
        with self._provider.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM einschreibung
                WHERE student_id = ? AND status = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (student_id, StatusEinschreibung.AKTIV.value),
            ).fetchone()
        return self._row_to_model(row) if row else None

    def alle_fuer_student(self, student_id: int) -> Iterable[Einschreibung]:
        with self._provider.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, student_id, start_datum, ziel_enddatum, ziel_notenschnitt, status, studiengang_id
                FROM einschreibung
                WHERE student_id=? ORDER BY id DESC
                """,
                (student_id,),
            ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_id(self, eid: int) -> Optional[Einschreibung]:
        with self._provider.connect() as conn:
            row = conn.execute("SELECT * FROM einschreibung WHERE id=?", (eid,)).fetchone()
        return self._row_to_model(row) if row else None
