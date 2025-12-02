# db/repositories/einschreibung_repository.py
"""
Interface für Einschreibungen (speichert u. a. Studienziele pro Student).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Iterable
from models.einschreibung import Einschreibung

class EinschreibungRepository(ABC):
    """Abstraktes Repository für Einschreibungen."""

    @abstractmethod
    def get_by_id(self, einschreibung_id: int) -> Optional[Einschreibung]:
        """Liefert eine Einschreibung oder None"""
        raise NotImplementedError

    @abstractmethod
    def get_active_for_student(self, student_id: int) -> Optional[Einschreibung]: 
        """Liefert die aktive Einschreibung für einen Studenten oder None, falls nicht vorhanden."""
        raise NotImplementedError
    
    @abstractmethod
    def list_by_student(self, student_id: int) -> Iterable[Einschreibung]: 
        """Liefert alle Einschreibungen für einen Studenten."""
        raise NotImplementedError
    
    @abstractmethod
    def create(self, e: Einschreibung) -> int: 
        """Erstellt eine Einschreibung und gibt die neue ID zurück."""
        raise NotImplementedError
    
    @abstractmethod
    def update(self, e: Einschreibung) -> None: 
        """Aktualisiert eine bestehende Einschreibung (per id)."""
        raise NotImplementedError
