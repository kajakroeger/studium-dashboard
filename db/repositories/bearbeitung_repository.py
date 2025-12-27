from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Optional
from models.bearbeitung import Bearbeitung


class BearbeitungRepository(ABC):
    """
    📦 LAGERVERWALTUNG (Bearbeitung)
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
    def get_by_id(self, bearbeitung_id: int) -> Optional[Bearbeitung]: 
        """Liefert eine Bearbeitung oder None, falls nicht vorhanden."""
        raise NotImplementedError
    
    @abstractmethod
    def list_by_student(self, student_id: int) -> Iterable[Bearbeitung]:
        """Liefert Liste von Bearbeitungen eines Studenten"""
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
