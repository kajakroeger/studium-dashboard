# db/repositories/bearbeitung_repository.py
"""
Interface für Bearbeitung-Entitäten.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Optional
from models.bearbeitung import Bearbeitung


class BearbeitungRepository(ABC):
    """Abstraktes Repository für Bearbeitungen."""

    @abstractmethod
    def get_by_id(self, bearbeitung_id: int) -> Optional[Bearbeitung]: 
        """Liefert eine Bearbeitung oder None, falls nicht vorhanden."""
        raise NotImplementedError
    
    @abstractmethod
    def all_for_student(self, student_id: int) -> Iterable[Bearbeitung]: 
        """Liefert alle Bearbeitungen für einen Studenten."""
        raise NotImplementedError
    
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
