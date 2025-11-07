# db/repositories/studiengang_repository.py
"""
Interface für Studiengang-Zugriffe.
"""
from abc import ABC, abstractmethod
from typing import Optional
from models import Studiengang

class StudiengangRepository(ABC):
    """Interface für Studiengang-Repository."""

    @abstractmethod
    def create(self, s: Studiengang) -> int: 
        """Legt einen neuen Studiengang an und gibt die ID zurück."""
    
    @abstractmethod
    def get_by_id(self, sid: int) -> Optional[Studiengang]: 
        """Liefert den Studiengang mit der gegebenen ID oder None."""

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Studiengang]: 
        """Liefert den Studiengang mit dem gegebenen Namen oder None."""
