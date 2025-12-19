# db/repositories/kurs_repository.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Optional
from models.kurs import Kurs


class KursRepository(ABC):
    """
    📦 LAGERVERWALTUNG (Kurs)
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
    def get_by_id(self, kurs_id: int) -> Optional[Kurs]: 
        """Liefert einen Kurs oder None, falls nicht vorhanden."""
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> Iterable[Kurs]: 
        """Liefert alle Kurse (ggf. paginiert, hier der Einfachheit halber vollständige Liste)."""
        raise NotImplementedError
    
    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """Prüft, ob ein Kurs mit diesem Namen existiert."""
        raise NotImplementedError
    
    @abstractmethod
    def exists_by_kuerzel(self, kurs_kuerzel: str) -> bool:
        """Prüft, ob ein Kurs mit diesem Kürzel existiert"""

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
    


