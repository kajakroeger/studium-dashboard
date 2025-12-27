# db/repositories/student_repository.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Optional
from models import Student


class StudentRepository(ABC):
    """
    📦 LAGERVERWALTUNG (Student)
    - legt fest, welche Lager-Aktionen für die Zutat möglich sind, z.B.:
      - finden (get_by_id)
      - hinzufügen (create)
      - entsorgen (delete)

    Technisch:
    - abstraktes Interface (Vertrag), keine SQLite-Details
    - entkoppelt Services & UI von der konkreten Datenbank
    - konkrete Implementierungen (z.B. SQLiteKursRepository) setzen diesen Vertrag um
    """
    @abstractmethod
    def get_by_id(self, student_id: int) -> Optional[Student]:
        """Liefert einen Studenten oder None, falls nicht vorhanden."""
        raise NotImplementedError

    @abstractmethod
    def all(self) -> Iterable[Student]:
        """Liefert alle Studenten (ggf. paginiert, hier der Einfachheit halber vollständige Liste)."""
        raise NotImplementedError

    @abstractmethod
    def create(self, student: Student) -> int:
        """Erstellt einen Datensatz und gibt die neue ID zurück."""
        raise NotImplementedError

    @abstractmethod 
    def update(self, student: Student) -> None:
        """Aktualisiert einen bestehenden Datensatz (per id)."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, student_id: int) -> None:
        """Löscht einen Datensatz (falls vorhanden, ansonsten no-op)."""
        raise NotImplementedError
