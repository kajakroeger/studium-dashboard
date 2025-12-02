# db/repositories/bearbeitung_repository.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Optional
from models.bearbeitung import Bearbeitung


class BearbeitungRepository(ABC):
    """Repository für Bearbeitungen mit konsistenten Methodennamen."""



    #TODO
    @abstractmethod
    def get_for_student_and_course_with_submission(
        self, student_id: int, kurs_id: int
    ) -> Optional[Bearbeitung]:
        """
        NEU: Explizite Methode für "Bearbeitung mit Abgabe".
        Ersetzt die lange Methode in SQLiteBearbeitungRepository.
        """




    @abstractmethod
    def get_by_id(self, bearbeitung_id: int) -> Optional[Bearbeitung]: 
        """Liefert eine Bearbeitung oder None, falls nicht vorhanden."""
        raise NotImplementedError
    
    # TODO 
    # @abstractmethod
    # def list_by_student(self, student_id: int) -> Iterable[Bearbeitung]: 
    #     """Liefert alle Bearbeitungen für einen Studenten."""
    #     raise NotImplementedError
    
    @abstractmethod
    def create(self, b: Bearbeitung) -> int: 
        """Erstellt einen Datensatz und gibt die neue ID zurück."""
        raise NotImplementedError
    
    @abstractmethod
    def update(self, b: Bearbeitung) -> None: 
        """Aktualisiert einen bestehenden Datensatz (per id)."""
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, bearbeitung_id: int) -> None: 
        """Löscht einen Datensatz (falls vorhanden, ansonsten no-op)."""
        raise NotImplementedError
