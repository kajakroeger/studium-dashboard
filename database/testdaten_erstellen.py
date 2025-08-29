"""
Die Datei fügt Testdaten in die Tabellen 'kurs' und 'bearbeitung' in die Testdatenbank 'studium.db' ein.
Zuerst werden Beispiel-Kurse eingefügt. Anschließend werden Bearbeitungen mit Startdatum, Abgabedatum und Status
hinzugefügt und mit den entsprechenden Kursen verknüpft.

"""

import sqlite3

con = sqlite3.connect("studium_test.db")
cur = con.cursor()

# Kurse hinzufügen
kurse = [
    ("Programmierung", "PRG101", 5, "Dr. Müller"),
    ("Mathematik", "MATH101", 6, "Prof. Schmidt"),
    ("Datenbanken", "DB101", 5, "Dr. Weber"),
    ("Grundlagen der industriellen Softwaretechnik", "SWT101", 6, "Prof. Keller"),
    ("Requirements Engineering", "REQ101", 5, "Dr. Braun"),
    ("Spezifikation", "SPZ101", 5, "Prof. Fischer"),
    ("Einführung in das wissenschaftliche Arbeiten für IT und Technik", "WISS101", 3, "Dr. König"),
]

for name, kuerzel, ects, tutor in kurse:
    cur.execute(
        "INSERT OR IGNORE INTO kurs (name, ects) VALUES (?, ?)", 
        (name, ects)
    )

# IDs für Bearbeitung holen
def kurs_id(name):
    row = cur.execute("SELECT id FROM kurs WHERE name=?", (name,)).fetchone()
    return row[0]

# Bearbeitungen hinzufügen
bearbeitungen = [
    ("Programmierung", "2025-01-05", "2025-02-02", "abgeschlossen"),
    ("Mathematik", "2025-02-06", "2025-03-03", "abgeschlossen"),
    ("Datenbanken", "2025-03-05", "2025-03-30", "aktiv"),
    ("Grundlagen der industriellen Softwaretechnik", "2025-04-06", "2025-05-03", "inaktiv"),
    ("Requirements Engineering", "2025-05-07", "2025-05-30", "pruefung_eingereicht"),
    ("Spezifikation", "2025-06-01", "2025-06-28", "abgeschlossen"),
    ("Einführung in das wissenschaftliche Arbeiten für IT und Technik", "2025-07-06", "2025-08-03", "aktiv"),
]

for kname, start, ende, status in bearbeitungen:
    cur.execute(
        "INSERT INTO bearbeitung (kurs_id, start_datum, abgabe_datum, status) VALUES (?,?,?,?)",
        (kurs_id(kname), start, ende, status)
    )

con.commit()
con.close()
print("OK – Testdaten für 'kurs' und 'bearbeitung' eingefügt.")
