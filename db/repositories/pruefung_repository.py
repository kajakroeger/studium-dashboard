# db/repositories/pruefung_repository.py
"""
Interface für Pruefung-Entitäten.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from models.pruefung import Pruefung


class PruefungRepository(ABC):
    """Abstraktes Repository für Pruefungen."""
    
    @abstractmethod
    def get_by_id(self, pruefung_id: int) -> Optional[Pruefung]: 
        """Liefert eine Pruefung oder None, falls nicht vorhanden."""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_bearbeitung_id(self, bearbeitung_id: int) -> Optional[Pruefung]: 
        """Liefert eine Pruefung anhand der zugehörigen Bearbeitung oder None, falls nicht vorhanden."""
        raise NotImplementedError
    
    @abstractmethod
    def create(self, p: Pruefung) -> int: 
        """Erstellt einen Datensatz und gibt die neue ID zurück."""
        raise NotImplementedError
    
    @abstractmethod
    def update(self, p: Pruefung) -> None: 
        """Aktualisiert einen bestehenden Datensatz (per id)."""
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, pruefung_id: int) -> None: 
        """Löscht einen Datensatz (falls vorhanden, ansonsten no-op)."""
        raise NotImplementedError
