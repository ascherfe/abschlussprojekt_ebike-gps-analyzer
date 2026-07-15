# E-Bike GPS Analyse

## Projektbeschreibung

Dieses Projekt wurde im Rahmen des Abschlussprojekts im Fach Programmieren erstellt.

Das Programm analysiert GPS-Daten einer E-Bike-Fahrt und berechnet verschiedene physikalische Größen wie Geschwindigkeit, Steigung, Motorleistung, Motorstrom und den Akkuladestand. Zusätzlich werden Diagramme erstellt und automatisch ein PDF-Ergebnisbericht generiert.

---

## Voraussetzungen

Für die Ausführung werden benötigt:

- Python 3.10 oder neuer
- pip
- Eine Python-Entwicklungsumgebung (z.B. Visual Studio Code)

Es wird empfohlen, das Projekt in einer virtuellen Umgebung (venv) auszuführen.

---

## Installation

Zuerst alle benötigten Bibliotheken installieren:

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

---

## Autoren

- Entwickler A: Ascher Felix
- Entwickler B: Fasser Maximilian