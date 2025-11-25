# db/repositories/sqlite_bearbeitung_repository.py
"""
SQLite-Repo für Bearbeitung (CRUD + Schema-Ensure/Migration).
Achtet auf:
- korrekte SQL-Strings (Leerzeichen!)
- idempotente Migration (Spalten prüfen)
- Enum-Mapping für StatusBearbeitung
- ISO-String <-> date konvertieren
"""

from __future__ import annotations
from typing import Iterable, Optional
from datetime import date

from db.connection_provider import ConnectionProvider
from db.repositories.bearbeitung_repository import BearbeitungRepository
from models.bearbeitung import Bearbeitung, StatusBearbeitung


def _parse_date(val: Optional[str]) -> Optional[date]:
    return date.fromisoformat(val) if val else None

def _to_str(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


class SQLiteBearbeitungRepository(BearbeitungRepository):
    def __init__(self, provider: ConnectionProvider) -> None:
        self._provider = provider
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Tabelle anlegen + minimale Migrationen (idempotent)."""
        with self._provider.connect() as conn:
            # Basistabelle
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bearbeitung (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    kurs_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    plan_start TEXT,
                    plan_end TEXT,
                    start_datum TEXT,
                    abgabe_datum TEXT
                )
            """)
            # Migrationen: fehlende Spalten nachrüsten (falls die Tabelle älter ist)
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(bearbeitung)")}
            add_cols = []
            if "plan_start" not in cols:
                add_cols.append("ALTER TABLE bearbeitung ADD COLUMN plan_start TEXT;")
            if "plan_end" not in cols:
                add_cols.append("ALTER TABLE bearbeitung ADD COLUMN plan_end TEXT;")
            if "start_datum" not in cols:
                add_cols.append("ALTER TABLE bearbeitung ADD COLUMN start_datum TEXT;")
            if "abgabe_datum" not in cols:
                add_cols.append("ALTER TABLE bearbeitung ADD COLUMN abgabe_datum TEXT;")
            if "status" not in cols:
                add_cols.append("ALTER TABLE bearbeitung ADD COLUMN status TEXT NOT NULL DEFAULT 'inaktiv';")

            for stmt in add_cols:
                conn.execute(stmt)
            conn.commit()

            # WICHTIG: Falls die Tabelle historisch OHNE 'id' angelegt wurde, kann SQLite das nicht einfach ändern.
            # In dem Fall bitte DB löschen (Dev) oder: Daten migrieren (CREATE TMP + COPY + DROP + RENAME).

    # ------------------- CRUD -------------------

    def get_by_id(self, bearbeitung_id: int) -> Optional[Bearbeitung]:
        with self._provider.connect() as conn:
            row = conn.execute(
                "SELECT id, student_id, kurs_id, status, plan_start, plan_end, start_datum, abgabe_datum "
                "FROM bearbeitung WHERE id = ?",
                (bearbeitung_id,),
            ).fetchone()
        return self._row_to_model(row) if row else None

    def einschreibungen_fuer_student(self, student_id: int) -> Iterable[Bearbeitung]:
        with self._provider.connect() as conn:
            rows = conn.execute(
                "SELECT id, student_id, kurs_id, status, plan_start, plan_end, start_datum, abgabe_datum "
                "FROM bearbeitung WHERE student_id = ? ORDER BY start_datum DESC",
                (student_id,),
            ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def create(self, b: Bearbeitung) -> int:
        with self._provider.connect() as conn:
            cur = conn.execute(
                "INSERT INTO bearbeitung "
                "(student_id, kurs_id, status, plan_start, plan_end, start_datum, abgabe_datum) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    b.student_id,
                    b.kurs_id,
                    b.status.value,
                    _to_str(b.plan_start),
                    _to_str(b.plan_end),
                    _to_str(b.start_datum),
                    _to_str(b.abgabe_datum),
                ),
            )
            conn.commit()
            new_id = int(cur.lastrowid)  # type: ignore[arg-type]
        b.id = new_id
        return new_id

    def update(self, b: Bearbeitung) -> None:
        if b.id is None:
            raise ValueError("Bearbeitung.update: id fehlt.")
        with self._provider.connect() as conn:
            conn.execute(
                "UPDATE bearbeitung SET "
                "student_id = ?, kurs_id = ?, status = ?, "
                "plan_start = ?, plan_end = ?, start_datum = ?, abgabe_datum = ? "
                "WHERE id = ?",
                (
                    b.student_id,
                    b.kurs_id,
                    b.status.value,
                    _to_str(b.plan_start),
                    _to_str(b.plan_end),
                    _to_str(b.start_datum),
                    _to_str(b.abgabe_datum),
                    b.id,
                ),
            )
            conn.commit()

    def delete(self, bearbeitung_id: int) -> None:
        with self._provider.connect() as conn:
            conn.execute("DELETE FROM bearbeitung WHERE id = ?", (bearbeitung_id,))
            conn.commit()

    # ------------------- Mapping -------------------

    @staticmethod
    def _row_to_model(row) -> Bearbeitung:
        return Bearbeitung(
            id=int(row["id"]),
            student_id=int(row["student_id"]),
            kurs_id=int(row["kurs_id"]),
            status=StatusBearbeitung(row["status"]),
            plan_start=_parse_date(row["plan_start"]),
            plan_end=_parse_date(row["plan_end"]),
            start_datum=_parse_date(row["start_datum"]),
            abgabe_datum=_parse_date(row["abgabe_datum"]),
        )
