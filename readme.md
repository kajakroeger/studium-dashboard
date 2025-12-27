# 🎓 Studium Dashboard – Dein persönlicher Studien-Tracker

Ein interaktives Dashboard zur Planung, Nachverfolgung und Auswertung des eigenen Studiums – entwickelt mit Python, Streamlit und einer klar getrennten Architektur aus Domänenlogik, Services und UI.

## Hintergrund
Das **Studium Dasboard** richtet sich insbesondere an Studierende, die ein Fernstudium absolvieren und ihre Lernzeiten und Prüfungen selbst organisieren. Ohne eine strukturierte Übersicht über den aktuellen Stand, kann es jedoch schwer fallen den Fortschritt bezüglich des erfolgreichen Abschlusses einzuschätzen. 

🧑‍🎓 Für wen ist dieses Projekt gedacht?
Dieses Projekt richtet sich an Studierende, die:
- ihren Studienfortschritt (ECTS, Kurse, Prüfungen, Noten) strukturiert verfolgen möchten
- Ziele wie Abschlussdatum oder Ziel-Notenschnitt im Blick behalten wollen
<br></br>

## ✨ Features
| Feature                                 | Beschreibung                                |
|-----------------------------------------|---------------------------------------------|
| 🎯 Studienziele                         | die vom Studierenden gesetztes Zieldatum und Ziel-Notenschnitt       |
| 📊 Status-Übersicht der Studienziele    | aktueller Stand und Prognose zum Erreichen der Ziele                 |
| 📊 Status-Übersicht                     | erreichte ECTS, aktueller Notenschnitt, Anzahl offener ECTS und durchschnittliche Bearbeitungszeit |
| 📈 Burndown-Chart                       | Studienfortschritt über Zeit  |
| 📈 Notenverlauf                         | Verlauf der erreichten Noten mit Verlauf des Notendurchschnitts      |
| 📊 Bearbeitungsverlauf                  | tatsächliche Bearbeitungszeit pro abgeschlossenen Kurs und Verlauf der durchschnittlichen Bearbeitungszeit |
| 🗓️ Kursplan (Gantt-ähnlich)             | Einplanung und tatsächliche Start- und Abschlussdatum der Kurse |
| 🧑‍🎓 Mehrere Studiengänge                 | pro Student sind mehrere Studiengänge möglich|


<br></br>

## verwendete Technologien

| Technologie           | Beschreibung                                |
|-----------------------|---------------------------------------------|
| SQLite                | relationale, dateibasierte Datenbank        |
| venv                  | Virtuelle Umgebung zur Verwaltung projekt-spezifischer Pakete und Abhängigkeiten, unabhängig von der globalen Python-Installation  |
| pandas                | zur Datenaufbereitung und -analyse          |
| plotly                | interaktive Diagramme und Visualisierungen  |
| streamlit             | User Interface                              |
| Jupyter Notebook      | Machbarkeitsprüfung und Dokumentation       |

<br></br>

## 🛠️ Voraussetzung
- Python 3.13.5 oder höher
<br></br>


## ⚙️ Installation & Nutzung
1. Repository klonen
 ```bash
 git clone https://github.com/DEIN-USERNAME/studium-dashboard.git
 cd studium-dashboard
 ```


2. Virtuelle Umgebung erstellen und aktivieren

```bash
# Windows
python -m venv venv 
venv\Scripts\activate        

```
```bash
# Linus/Mac
python -m venv venv 
source venv/bin/activate     

```

3. Abhängigkeiten installieren
```bash
pip install -r requeriements.txt
```   

4. Test-Datenbank einrichten
```bash
python steup_test_db.py
python testdaten_erstellen.py
```

5. Dashboard starten
```bash
streamlit run app.py
```
