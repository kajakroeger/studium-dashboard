
"""
Die Datei erstellt eine SQLite-Datenbank 'studium_test.db' als Test-Datenbank mit zwei Tabellen:

- kurs: speichert Informationen zu einzelnen Kursen (Name, ECTS, Note).
- bearbeitung: speichert Bearbeitungen von Kursen (Startdatum, Abgabedatum, Status)
  und ist über einen Fremdschlüssel mit der Tabelle kurs verknüpft.

Zusätzlich wird ein eindeutiger Index auf (name, ects) in kurs angelegt, 
um doppelte Einträge zu verhindern. Am Ende wird die erfolgreiche Erstellung bestätigt.

""" 

import sqlite3

con = sqlite3.connect("studium_test.db")
cur = con.cursor()

cur.execute("PRAGMA foreign_keys = ON;")

# Tabelle kurs
cur.execute("""
CREATE TABLE IF NOT EXISTS kurs(
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ects INTEGER NOT NULL,
    note REAL
)
""")

# Tabelle bearbeitung
cur.execute("""
CREATE TABLE IF NOT EXISTS bearbeitung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kurs_id INTEGER NOT NULL,
    start_datum TEXT,
    abgabe_datum TEXT,
    status TEXT,
    FOREIGN KEY (kurs_id) REFERENCES kurs(id)
)
""")

# Index zur Absicherung von Duplikaten
cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_kurs_name_ects ON kurs(name, ects);")

con.commit()
con.close()
print("OK – Tabellen 'kurs' und 'bearbeitung' angelegt.")
