from typing import Optional, Iterable
from datetime import date
from models.einschreibung import Einschreibung, StatusEinschreibung

def _parse_date(val: Optional[str]) -> Optional[date]:
    return date.fromisoformat(val) if val else None

def _to_str(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


class SQLiteEinschreibungRepository:
    def __init__(self, provider) -> None:
        self._provider = provider
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._provider.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS einschreibung (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    studiengang_id INTEGER NOT NULL,
                    start_datum TEXT NOT NULL,
                    ziel_enddatum TEXT,
                    ziel_notenschnitt REAL,
                    status TEXT NOT NULL,
                    end_datum TEXT,
                    abschluss_note REAL
                )
            """)
             # Migration: Fehlende Spalten nachrüsten
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(einschreibung)")}
            if "end_datum" not in cols:
                conn.execute("ALTER TABLE einschreibung ADD COLUMN end_datum TEXT;")
            if "abschluss_note" not in cols:
                conn.execute("ALTER TABLE einschreibung ADD COLUMN abschluss_note REAL;")

            conn.commit()

    def get_by_id(self, einschreibung_id: int) -> Optional[Einschreibung]:
        with self._provider.connect() as conn:
            row = conn.execute(
                "SELECT id, student_id, studiengang_id, start_datum, ziel_enddatum, "
                "ziel_notenschnitt, status, end_datum, abschluss_note "
                "FROM einschreibung WHERE id = ?",
                (einschreibung_id,),
            ).fetchone()
        return self._row_to_model(row) if row else None

    def get_active_for_student(self, student_id: int) -> Optional[Einschreibung]:
        with self._provider.connect() as conn:
            row = conn.execute(
                "SELECT id, student_id, studiengang_id, start_datum, ziel_enddatum, "
                "ziel_notenschnitt, status, end_datum, abschluss_note "
                "FROM einschreibung WHERE student_id = ? AND status = 'aktiv' "
                "ORDER BY start_datum DESC LIMIT 1",
                (student_id,),
            ).fetchone()
        return self._row_to_model(row) if row else None

    def list_by_student(self, student_id: int) -> Iterable[Einschreibung]:
        with self._provider.connect() as conn:
            rows = conn.execute(
                "SELECT id, student_id, studiengang_id, start_datum, ziel_enddatum, "
                "ziel_notenschnitt, status, end_datum, abschluss_note "
                "FROM einschreibung WHERE student_id = ? ORDER BY start_datum DESC",
                (student_id,),
            ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def create(self, e: Einschreibung) -> int:
        with self._provider.connect() as conn:
            cur = conn.execute(
                "INSERT INTO einschreibung "
                "(student_id, studiengang_id, start_datum, ziel_enddatum, "
                "ziel_notenschnitt, status, end_datum, abschluss_note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    e.student_id,
                    e.studiengang_id,
                    _to_str(e.start_datum),
                    _to_str(e.ziel_enddatum),
                    e.ziel_notenschnitt,
                    e.status.value,
                    _to_str(e.end_datum),
                    e.abschluss_note,
                ),
            )
            conn.commit()
            new_id = int(cur.lastrowid)
        e.id = new_id
        return new_id

    def update(self, e: Einschreibung) -> None:
        if e.id is None:
            raise ValueError("Einschreibung.update: id fehlt.")
        with self._provider.connect() as conn:
            conn.execute(
                "UPDATE einschreibung SET "
                "student_id = ?, studiengang_id = ?, start_datum = ?, "
                "ziel_enddatum = ?, ziel_notenschnitt = ?, status = ?, "
                "end_datum = ?, abschluss_note = ? "
                "WHERE id = ?",
                (
                    e.student_id,
                    e.studiengang_id,
                    _to_str(e.start_datum),
                    _to_str(e.ziel_enddatum),
                    e.ziel_notenschnitt,
                    e.status.value,
                    _to_str(e.end_datum),
                    e.abschluss_note,
                    e.id,
                ),
            )
            conn.commit()

    def delete(self, einschreibung_id: int) -> None:
        with self._provider.connect() as conn:
            conn.execute("DELETE FROM einschreibung WHERE id = ?", (einschreibung_id,))
            conn.commit()

    @staticmethod
    def _row_to_model(row) -> Einschreibung:
        """KRITISCH: ID muss korrekt gemappt werden!"""
        return Einschreibung(
            id=int(row["id"]),  
            student_id=int(row["student_id"]),
            studiengang_id=int(row["studiengang_id"]),
            start_datum=_parse_date(row["start_datum"]),
            ziel_enddatum=_parse_date(row["ziel_enddatum"]),
            ziel_notenschnitt=float(row["ziel_notenschnitt"]) if row["ziel_notenschnitt"] else None,
            status=StatusEinschreibung(row["status"]),
            end_datum=_parse_date(row["end_datum"]),
            abschluss_note=float(row["abschluss_note"]) if row["abschluss_note"] else None,
        )