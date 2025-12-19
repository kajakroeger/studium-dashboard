from abc import ABC, abstractmethod
from typing import Iterable, Optional
from models import Studiengang

class StudiengangRepository(ABC):
    """
    📦 LAGERVERWALTUNG (Studiengang)
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
    def create(self, s: Studiengang) -> int: 
        """Legt einen neuen Studiengang an und gibt die ID zurück."""
    
    @abstractmethod
    def get_by_id(self, sid: int) -> Optional[Studiengang]: 
        """Liefert den Studiengang mit der gegebenen ID oder None."""

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Studiengang]: 
        """Liefert den Studiengang mit dem gegebenen Namen oder None."""

    @abstractmethod
    def list_all(self) -> Iterable[Studiengang]:
        """Liefert alle Studiengänge"""
