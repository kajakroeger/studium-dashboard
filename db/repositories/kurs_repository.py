# db/repositories/kurs_repository.py
"""
Definiert das Interface für den Zugriff auf Kurs-Entitäten.
Die UI/Services hängen nur von diesem Interface ab – nicht von SQLite."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Optional
from models.kurs import Kurs


class KursRepository(ABC):
    """Abstraktes Repository für Kurse."""

    @abstractmethod
    def get_by_id(self, kurs_id: int) -> Optional[Kurs]: 
        """Liefert einen Kurs oder None, falls nicht vorhanden."""
        raise NotImplementedError

    @abstractmethod
    def all(self) -> Iterable[Kurs]: 
        """Liefert alle Kurse (ggf. paginiert, hier der Einfachheit halber vollständige Liste)."""
        raise NotImplementedError
    
    @abstractmethod
    def create(self, kurs: Kurs) -> int: 
        """Erstellt einen Datensatz und gibt die neue ID zurück."""
        raise NotImplementedError
    
    @abstractmethod
    def update(self, kurs: Kurs) -> None: 
        """Aktualisiert einen bestehenden Datensatz (per id)."""
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, kurs_id: int) -> None: 
        """Löscht einen Datensatz (falls vorhanden, ansonsten no-op)."""
        raise NotImplementedError
