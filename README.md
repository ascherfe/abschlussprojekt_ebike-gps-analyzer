# E-Bike GPS Analyse

## Projektbeschreibung

Dieses Projekt wurde im Rahmen des Abschlussprojekts in der Vorlesung Programmieren I erstellt.

Das Programm analysiert GPS-Daten einer E-Bike-Fahrt und berechnet verschiedene physikalische Größen wie Geschwindigkeit, Steigung, Motorleistung, Motorstrom und den Akkuladestand. Zusätzlich werden einige hilfreiche Diagramme erstellt, Wetterdaten analysiert und automatisch ein PDF-Fahrtenbericht generiert.

---

## Voraussetzungen

Für die Ausführung werden benötigt:

- Python 3.10 oder neuer
- pip
- Eine Python-Entwicklungsumgebung (z.B. Visual Studio Code)

---

## Installation

Es wird empfohlen, das Projekt in einer virtuellen Umgebung (venv) auszuführen, um Paketkonflikte zu vermeiden. 

1. Repository klonen und den Projektordner im Terminal der IDE öffnen

2. Virtuelle Umgebung erstellen & aktivieren:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3 Alle benötigten Bibliotheken aus der requirements.txt-Datei installieren:

```bash
pip install -r requirements.txt
```


## Projekt starten

Das Hauptprogramm wird mit folgendem Befehl gestartet:

```bash
python main.py
```

Für die Parameterstudie:

```bash
python parameter_study.py
```

## Implementierte Erweiterungen

- Wetter-Integration: Automatischer Abruf von historischen Winddaten während der Fahrt mittels Open-Meteo API
- Erweiterte Fahrphysik: Berücksichtigung vom Luftwiderstand und Rollwiderstand
- Automatisierte Parameterstudie: Vergleich von drei Systemgewichten und Reifentypen
- Erweiterte Plots für die Datenvisualisierung: Detailiertes Höhenprofil über die Fahrstrecke, Höhenprofil mit Steigungsanzeige und Plot mit Windeinfluss 
- Automatischer PDF-Ergebnisbericht


## Eingabedaten

Die Eingabedatei muss sich unter folgendem Pfad befinden:

```
data/raw/final_project_input_data.csv
```

Der Dateiname und der Speicherort sollten nicht verändert werden.


## Ausgabe

Nach erfolgreicher Ausführung werden folgende Dateien erzeugt:

- Diagramme im Ordner

```
data/processed/plots/
```

- Simulationsergebnisse

```
data/processed/simulation_results.csv
```

- PDF-Ergebnisbericht

```
data/processed/ebike_ergebnisbericht.pdf
```


## Hinweise

- Das Programm muss aus dem Hauptordner des Projekts gestartet werden.
- Vor der ersten Ausführung müssen die Pakete aus der `requirements.txt` installiert werden.
- Die Eingabedatei muss sich im Ordner `data/raw` befinden.
- Die erzeugten Diagramme und Berichte werden bei einer erneuten Ausführung überschrieben.
- Um im Ergebnisbericht auch das Plot der Parameterstudie einzufügen, muss die Parameterstudie vor der Main-Datei ausgeführt werden.

---

## Autoren

- Entwickler A: Ascher Felix
- Entwickler B: Fasser Maximilian
