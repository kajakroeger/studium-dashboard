# db/repositories/sqlite_pruefung_repository.py
"""
SQLite-Skelett für PruefungRepository.
Beachtet Enum-Konvertierung für Pruefungsform und bool/ints.
"""

from __future__ import annotations
from typing import Optional

from db import ConnectionProvider
from models.pruefung import Pruefung, Pruefungsform
from models.bearbeitung import StatusBearbeitung
from .pruefung_repository import PruefungRepository


class SQLitePruefungRepository(PruefungRepository):
    def __init__(self, provider: ConnectionProvider) -> None:
        self._provider = provider
        self._ensure_table()

    # legt Datenbanktabelle an, falls sie noch nicht existiert
    def _ensure_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS pruefung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bearbeitung_id INTEGER NOT NULL,
            pruefungsform TEXT NOT NULL,
            note REAL,
            versuch_nr INTEGER NOT NULL DEFAULT 0,
            bestanden INTEGER,         -- NULL/0/1
            letzter_versuch INTEGER    -- 0/1
        );
        """
        with self._provider.connect() as conn:
            conn.execute(sql)
            conn.commit()


    # Public API
    def get_by_id(self, pruefung_id: int) -> Optional[Pruefung]:
        with self._provider.connect() as conn:
            row = conn.execute(
                "SELECT id, bearbeitung_id, pruefungsform, note, versuch_nr, bestanden, letzter_versuch "
                "FROM pruefung WHERE id=?",
                (pruefung_id,),
            ).fetchone()
        return None if row is None else self._row_to_model(row)
    

    def get_by_bearbeitung_id(self, bearbeitung_id: int) -> Optional[Pruefung]:
        with self._provider.connect() as conn:
            row = conn.execute(
                "SELECT id, bearbeitung_id, pruefungsform, note, versuch_nr, bestanden, letzter_versuch "
                "FROM pruefung WHERE bearbeitung_id = ? LIMIT 1",
                (bearbeitung_id,),
            ).fetchone()
        return None if row is None else self._row_to_model(row)


    def create(self, p: Pruefung) -> int:
        with self._provider.connect() as conn:
            cur = conn.execute(
                "INSERT INTO pruefung (bearbeitung_id, pruefungsform, note, versuch_nr, bestanden, letzter_versuch) "
                "VALUES (?,?,?,?,?,?)",
                (
                    p.bearbeitung.id,
                    p.pruefungsform.value,
                    p.note,
                    p.versuch_nr,
                    None if p.bestanden is None else int(p.bestanden),
                    int(p.letzter_versuch),
                ),
            )
            conn.commit()
            new_id = int(cur.lastrowid)  # type: ignore[arg-type]
        p.id = new_id
        return new_id


    def update(self, p: Pruefung) -> None:
        with self._provider.connect() as conn:
            conn.execute(
                "UPDATE pruefung SET bearbeitung_id=?, pruefungsform=?, note=?, versuch_nr=?, bestanden=?, letzter_versuch=? "
                "WHERE id=?",
                (
                    p.bearbeitung.id,
                    p.pruefungsform.value,
                    p.note,
                    p.versuch_nr,
                    None if p.bestanden is None else int(p.bestanden),
                    int(p.letzter_versuch),
                    p.id,
                ),
            )
            conn.commit()


    def delete(self, pruefung_id: int) -> None:
        with self._provider.connect() as conn:
            conn.execute("DELETE FROM pruefung WHERE id=?", (pruefung_id,))
            conn.commit()

    # Mapping: Achtung – hier bräuchtest du die Bearbeitung (Objekt).
    # Vereinfachung: Wir setzen bearbeitung=None und laden sie im Service nach,
    # oder du gibst hier ein BearbeitungRepository rein. Fürs Grundgerüst setzen wir None.
    @staticmethod
    def _row_to_model(row) -> Pruefung:
        # Bearbeitung-Objekt wird später im Service aufgelöst (Lazy).
        from models.bearbeitung import Bearbeitung  # vermeiden von Zyklus im Kopf
        dummy_bearbeitung = Bearbeitung(
            id=row["bearbeitung_id"],
            kurs_id=-1,
            student_id=-1,
            start_datum=None,  # type: ignore[arg-type]
            status=StatusBearbeitung.INAKTIV,
        )
        return Pruefung(
            id=row["id"],
            bearbeitung=dummy_bearbeitung,
            pruefungsform=Pruefungsform(row["pruefungsform"]),
            note=row["note"],
            versuch_nr=row["versuch_nr"],
            bestanden=None if row["bestanden"] is None else bool(row["bestanden"]),
            letzter_versuch=bool(row["letzter_versuch"]),
        )
