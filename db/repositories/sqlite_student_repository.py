"""
Datei: db/repositories/sqlite_student_repository.py
Beschreibung:
SQLite-Implementierung des StudentRepository.
- nutzt den ConnectionProvider (bleibt dadurch auf Interface-Ebene DB-agnostisch)
- legt das Schema bei Bedarf automatisch an (idempotent)
- mappt DB-Zeilen (sqlite3.Row) zu Model-Objekten (Student)
"""

from __future__ import annotations
from typing import Iterable, Optional

# WICHTIG: innerhalb von db/... besser relative Importe verwenden:
from db import ConnectionProvider
from .student_repository import StudentRepository
from models import Student


class SQLiteStudentRepository(StudentRepository):
    """
    📦💁‍♂️ REGALMANAGER (Student) 
    - führt Aktionen mit der Zutat 'Student' aus z.B. finden, hinzufügen und entfernen,  

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
        """Erstellt die Tabelle 'student', sofern sie noch nicht existiert."""
        with self._provider.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS student (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    matrikelnummer TEXT NOT NULL UNIQUE,
                    email TEXT,
                    uni_email TEXT
                )
            """)
            conn.commit()

    # ------------------- CRUD -------------------

    def get_by_id(self, student_id: int) -> Optional[Student]:
        """Liest einen Studenten per ID; None, wenn nicht vorhanden."""
        with self._provider.connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, matrikelnummer, email, uni_email
                FROM student
                WHERE id = ?
                """,
                (student_id,),
            ).fetchone()
        return None if row is None else self._row_to_model(row)

    def all(self) -> Iterable[Student]:
        """Liefert alle Studenten, sortiert nach Nachname/Vorname."""
        with self._provider.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, matrikelnummer, email, uni_email
                FROM student
                ORDER BY name
                """
            ).fetchall()
        return [self._row_to_model(r) for r in rows]


    def create(self, student: Student) -> int:
        """
        Legt einen Studenten an ODER aktualisiert ihn, falls die Matrikelnummer bereits existiert.
        Gibt in beiden Fällen die ID zurück und setzt student.id.
        Diese Implementierung macht create() idempotent nach 'matrikelnummer'.
        """
        with self._provider.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO student (name, matrikelnummer, email, uni_email)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(matrikelnummer) DO UPDATE SET
                    name = excluded.name,
                    email = excluded.email,
                    uni_email = excluded.uni_email
                RETURNING id;
                """,
                (student.name, student.matrikelnummer, student.email, student.uni_email),
            )
            row = cur.fetchone()
            conn.commit()
        new_id = int(row["id"])  # type: ignore[index]
        student.id = new_id
        return new_id


    def update(self, student: Student) -> None:
        """Aktualisiert einen Studenten (per ID)."""
        with self._provider.connect() as conn:
            conn.execute(
                """
                UPDATE student
                SET name = ?, matrikelnummer = ?, email = ?, uni_email = ?
                WHERE id = ?
                """,
                (
                    student.name,
                    student.matrikelnummer,
                    student.email,
                    student.uni_email,
                    student.id,
                ),
            )
            conn.commit()

    def delete(self, student_id: int) -> None:
        """Löscht einen Studenten (wenn vorhanden)."""
        with self._provider.connect() as conn:
            conn.execute("DELETE FROM student WHERE id = ?", (student_id,))
            conn.commit()

    # ---------- Mapping-Helfer ----------

    @staticmethod
    def _row_to_model(row) -> Student:
        """Konvertiert eine sqlite3.Row in ein Student-Objekt."""
        return Student(
            id=row["id"],
            name=row["name"],
            matrikelnummer=row["matrikelnummer"],
            email=row["email"],
            uni_email=row["uni_email"],
        )
