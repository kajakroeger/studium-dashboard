# Studium Dashboard (Konzeptionsphase)

Das Studium Dashboard unterstützt dabei, das Studium zu einem von Studierenden selbst gewählten Zeitpunkt und gewünschtem Notendurchschnitt erfolgreich abzuschließen.

## Hintergrund
Das Dasboard richtet sich an Studierende, die ein Fernstudium absolvieren und ihre Lernzeiten und Prüfungen flexibel selbstgestalten können. Ohne eine strukturierte Übersicht über den aktuellen Stand, fällt es jedoch schwer den Fortschritt bezüglich des erfolgreichen Abschlusses einzuschätzen. 

Das Studium Dasboard gibt daher eine Übersicht über den aktuellen Stand des Studienfortschritts und liefert eine Prognose über den Abschluss des Studiums.
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
