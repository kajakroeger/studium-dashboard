# db/repositories/student_repository.py
"""
Definiert das Interface für den Zugriff auf Student-Entitäten.
Die UI/Services hängen nur von diesem Interface ab – nicht von SQLite.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Optional
from models import Student


class StudentRepository(ABC):
    """Abstraktes Repository für Studenten."""

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
