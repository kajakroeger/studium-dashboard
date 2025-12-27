# 🎓 Studium Dashboard – Dein persönlicher Studien-Tracker

Ein interaktives Dashboard zur Planung, Nachverfolgung und Auswertung des eigenen Studiums – entwickelt mit Python, Streamlit und einer klar getrennten Architektur aus Domänenlogik, Services und UI.

## Hintergrund
Das **Studium Dasboard** richtet sich insbesondere an Studierende, die ein Fernstudium absolvieren und ihre Lernzeiten und Prüfungen selbst organisieren. Ohne eine strukturierte Übersicht über den aktuellen Stand, kann es jedoch schwer fallen den Fortschritt bezüglich des erfolgreichen Abschlusses einzuschätzen. 

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

## 🤖 Verwendete Technologien

| Technologie           | Beschreibung                                |
|-----------------------|---------------------------------------------|
| SQLite                | relationale, dateibasierte Datenbank        |
| venv                  | Virtuelle Umgebung zur Verwaltung projekt-spezifischer Pakete und Abhängigkeiten, unabhängig von der globalen Python-Installation  |
| streamlit             | User Interface                              |
| pandas                | Projektvorbereitung: zur Datenaufbereitung und -analyse          |
| plotly                | Projektvorbereitung: interaktive Diagramme und Visualisierungen  |
| Jupyter Notebook      | Projektvorbereitung: Machbarkeitsprüfung und Dokumentation       |

<br></br>

## 🛠️ Voraussetzung
- Python 3.13.5 oder höher  

<br></br>

## 📁 Projektstrutur
<img width="925" height="716" alt="image" src="https://github.com/user-attachments/assets/57c50f11-8e85-4f9d-9408-850e02d97b05" />


<br></br>

## 🧑‍🍳 Code-Dokumentation mit Restaurant-Analogie
Das Dashboard ist im Rahmen eines Studium-Projekts entstanden. Zur besseren Verständlichkeit wurde eine Restaurant-/Küchenanalogie eingeführt. Diese Analogie dient ausschließlich der didaktischen Unterstützung und verdeutlicht die Rollen und Verantwortlichkeiten der einzelnen Komponenten, ohne die technische Architektur zu beeinflussen. Eine Beschreibung der Analogie findet sich unter jupyter_notebook_notes/restaurant_analogie.ipynb. 


<br></br>


## ⚙️ Installation & Nutzung
1. Repository klonen
 ```bash
 git clone https://github.com/kajakroeger/studium-dashboard.git
 cd studium-dashboard
 ```


2. Virtuelle Umgebung erstellen und aktivieren

```bash
# Windows
python -m venv venv 
venv\Scripts\Activate.ps1        

```
```bash
# Linus/Mac
python -m venv venv 
source venv/bin/activate     

```

3. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```   

4. Dashboard starten
```bash
streamlit run app.py
```
Nach dem Start öffnet sich das Dashboard automatisch im Browser.
Beim ersten Start wirst du durch ein Onboarding geführt (Student, Studiengang, Ziele).
