# db/repositories/sqlite_kurs_repository.py
from __future__ import annotations
from typing import Iterable, Optional

from db import ConnectionProvider
from models.kurs import Kurs
from .kurs_repository import KursRepository


class SQLiteKursRepository(KursRepository):
    """
    📦💁‍♂️ REGALMANAGER (Kurs) 
    - führt Aktionen mit der Zutat 'Kurs' aus z.B. finden, hinzufügen und entfernen  

    Technisch:
    - Konkreter SQLite-Adapter für KursRepository.
    - Nutzt ConnectionProvider (bleibt dadurch DB-agnostisch auf Interface-Ebene)
    - Verwendet über den ConnectionProvider sqlite3 
    - Enthält Mapping-Funktionen DB <-> Model
    """
    def __init__(self, provider: ConnectionProvider) -> None:
        self._provider = provider
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Erstellt die Tabelle 'kurs', sofern sie noch nicht existiert."""
        with self._provider.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kurs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    kurs_kuerzel TEXT NOT NULL,
                    ects INTEGER NOT NULL,
                    tutor TEXT,
                    semester INTEGER,
                    studiengang_id INTEGER NOT NULL
                );
            """)

            # Unique pro Studiengang
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_kurs_name_sg
                ON kurs(name, studiengang_id);
            """)
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_kurs_kuerzel_sg
                ON kurs(kurs_kuerzel, studiengang_id);
            """)

            conn.commit()

    # ------------------- CRUD -------------------

    def get_by_id(self, kurs_id: int) -> Optional[Kurs]:
        with self._provider.connect() as conn:
            row = conn.execute(
                "SELECT id, name, kurs_kuerzel, ects, tutor, semester, studiengang_id FROM kurs WHERE id=?",
                (kurs_id,),
            ).fetchone()
        return None if row is None else self._row_to_model(row)

    def list_all(self) -> Iterable[Kurs]:
        with self._provider.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, kurs_kuerzel, ects, tutor, semester, studiengang_id FROM kurs ORDER BY name"
            ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def create(self, kurs: Kurs) -> int:
        if self.exists_by_name(kurs.name, kurs.studiengang_id):
            raise ValueError("Kursname existiert bereits (in diesem Studiengang).")
        if self.exists_by_kuerzel(kurs.kurs_kuerzel, kurs.studiengang_id):
            raise ValueError("Kurskürzel existiert bereits (in diesem Studiengang).")

        with self._provider.connect() as conn:
            cur = conn.execute(
                "INSERT INTO kurs (name, kurs_kuerzel, ects, tutor, semester, studiengang_id) VALUES (?,?,?,?,?,?)",
                (kurs.name, kurs.kurs_kuerzel, kurs.ects, kurs.tutor, kurs.semester, kurs.studiengang_id),
            )
            conn.commit()
            new_id = int(cur.lastrowid)  
        kurs.id = new_id
        return new_id


    def update(self, kurs: Kurs) -> None:
        with self._provider.connect() as conn:
            conn.execute(
                "UPDATE kurs SET name=?, kurs_kuerzel=?, ects=?, tutor=?, semester=?, studiengang_id=? WHERE id=?",
                (kurs.name, kurs.kurs_kuerzel, kurs.ects, kurs.tutor, kurs.semester, kurs.studiengang_id, kurs.id),
            )
            conn.commit()

    def delete(self, kurs_id: int) -> None:
        with self._provider.connect() as conn:
            conn.execute("DELETE FROM kurs WHERE id=?", (kurs_id,))
            conn.commit()


    # ----- Existenzprüfungen -----
    def exists_by_name(self, name: str, studiengang_id: Optional[int] = None) -> bool:
        """Prüft, ob ein Kurs mit dem gegebenen Namen existiert (optional je Studiengang)."""
        name_norm = name.strip()
        if studiengang_id is None:
            sql = "SELECT 1 FROM kurs WHERE name = ? COLLATE NOCASE LIMIT 1;"
            params = (name_norm,)
        else:
            sql = "SELECT 1 FROM kurs WHERE name = ? COLLATE NOCASE AND studiengang_id = ? LIMIT 1;"
            params = (name_norm, studiengang_id)

        with self._provider.connect() as conn:
            return conn.execute(sql, params).fetchone() is not None


    def exists_by_kuerzel(self, kurs_kuerzel: str, studiengang_id: Optional[int] = None) -> bool:
        """Prüft, ob ein Kurs mit dem gegebenen Kürzel existiert (optional je Studiengang)."""
        kuerzel_norm = kurs_kuerzel.strip()
        if studiengang_id is None:
            sql = "SELECT 1 FROM kurs WHERE kurs_kuerzel = ? COLLATE NOCASE LIMIT 1;"
            params = (kuerzel_norm,)
        else:
            sql = "SELECT 1 FROM kurs WHERE kurs_kuerzel = ? COLLATE NOCASE AND studiengang_id = ? LIMIT 1;"
            params = (kuerzel_norm, studiengang_id)

        with self._provider.connect() as conn:
            return conn.execute(sql, params).fetchone() is not None


    @staticmethod
    def _row_to_model(row) -> Kurs:
        """Konvertiert eine sqlite3.Row in ein Kurs-Objekt."""
        return Kurs(
            id=int(row["id"]),
            name=row["name"],
            kurs_kuerzel=row["kurs_kuerzel"],
            ects=row["ects"],
            tutor=row["tutor"],
            semester=int(row["semester"]) if row["semester"] is not None else None,
            studiengang_id=row["studiengang_id"],
        )
