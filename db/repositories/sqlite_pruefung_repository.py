# db/repositories/sqlite_pruefung_repository.py
"""
SQLite-Implementierung für PruefungRepository.
Beachtet Enum-Konvertierung für Pruefungsform und bool/ints.
"""

from __future__ import annotations

from typing import Optional

from db import ConnectionProvider
from models.pruefung import Pruefung, Pruefungsform
from .pruefung_repository import PruefungRepository


class SQLitePruefungRepository(PruefungRepository):
    def __init__(self, provider: ConnectionProvider) -> None:
        self._provider = provider
        self._ensure_table()

    # Tabelle anlegen, falls noch nicht vorhanden
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

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get_by_id(self, pruefung_id: int) -> Optional[Pruefung]:
        with self._provider.connect() as conn:
            row = conn.execute(
                """
                SELECT id, bearbeitung_id, pruefungsform,
                       note, versuch_nr, bestanden, letzter_versuch
                FROM pruefung
                WHERE id = ?
                """,
                (pruefung_id,),
            ).fetchone()
        return None if row is None else self._row_to_model(row)

    def get_by_bearbeitung_id(self, bearbeitung_id: int) -> Optional[Pruefung]:
        """Liefert die (aktuelle) Prüfung zu einer Bearbeitung, falls vorhanden."""
        with self._provider.connect() as conn:
            row = conn.execute(
                """
                SELECT id, bearbeitung_id, pruefungsform,
                       note, versuch_nr, bestanden, letzter_versuch
                FROM pruefung
                WHERE bearbeitung_id = ?
                ORDER BY versuch_nr DESC
                LIMIT 1
                """,
                (bearbeitung_id,),
            ).fetchone()
        return None if row is None else self._row_to_model(row)

    def create(self, p: Pruefung) -> int:
        # bearbeitung_id muss gesetzt sein
        if getattr(p, "bearbeitung_id", None) is None:
            raise ValueError("Pruefung.create: bearbeitung_id fehlt")

        form = getattr(p.pruefungsform, "value", p.pruefungsform)

        bestanden_db = (
            None
            if getattr(p, "bestanden", None) is None
            else (1 if p.bestanden else 0)
        )
        letzter = 1 if getattr(p, "letzter_versuch", False) else 0
        versuch = int(getattr(p, "versuch_nr", 1) or 1)

        with self._provider.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO pruefung (
                    bearbeitung_id,
                    pruefungsform,
                    note,
                    versuch_nr,
                    bestanden,
                    letzter_versuch
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(p.bearbeitung_id),
                    form,
                    p.note,
                    versuch,
                    bestanden_db,
                    letzter,
                ),
            )
            conn.commit()
            p.id = int(cur.lastrowid)
            return p.id

    def update(self, p: Pruefung) -> None:
        if p.id is None:
            raise ValueError("Pruefung.update: id fehlt")

        form = getattr(p.pruefungsform, "value", p.pruefungsform)
        bestanden_db = (
            None
            if getattr(p, "bestanden", None) is None
            else (1 if p.bestanden else 0)
        )
        letzter = 1 if getattr(p, "letzter_versuch", False) else 0
        versuch = int(getattr(p, "versuch_nr", 1) or 1)

        with self._provider.connect() as conn:
            conn.execute(
                """
                UPDATE pruefung
                SET bearbeitung_id = ?,
                    pruefungsform  = ?,
                    note           = ?,
                    versuch_nr     = ?,
                    bestanden      = ?,
                    letzter_versuch= ?
                WHERE id = ?
                """,
                (
                    int(p.bearbeitung_id),
                    form,
                    p.note,
                    versuch,
                    bestanden_db,
                    letzter,
                    int(p.id),
                ),
            )
            conn.commit()

    def delete(self, pruefung_id: int) -> None:
        with self._provider.connect() as conn:
            conn.execute("DELETE FROM pruefung WHERE id = ?", (pruefung_id,))
            conn.commit()

    # ------------------------------------------------------------------ #
    # Row → Model
    # ------------------------------------------------------------------ #
    @staticmethod
    def _row_to_model(row) -> Pruefung:
        return Pruefung(
            id=int(row["id"]),
            bearbeitung_id=int(row["bearbeitung_id"]),
            pruefungsform=Pruefungsform(row["pruefungsform"]),
            note=row["note"],
            versuch_nr=int(row["versuch_nr"]),
            bestanden=(
                bool(row["bestanden"])
                if row["bestanden"] is not None
                else False
            ),
            letzter_versuch=bool(row["letzter_versuch"]),
        )
