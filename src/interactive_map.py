from pathlib import Path
import csv
import json
import math
import webbrowser


# ---------------------------------------------------------
# 1. Projektpfade
# ---------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

POSSIBLE_CSV_PATHS = [
    PROJECT_DIR / "data" / "raw" / "final_project_input_data.csv",
    PROJECT_DIR / "data" / "raw" / "simulation_results.csv",
    SCRIPT_DIR / "simulation_results.csv",
    PROJECT_DIR / "simulation_results.csv",
]

OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "interactive_route_3d.html"


# ---------------------------------------------------------
# 2. CSV-Datei suchen
# ---------------------------------------------------------

def find_csv_file():
    for csv_path in POSSIBLE_CSV_PATHS:
        if csv_path.exists():
            return csv_path

    print("Fehler: Es wurde keine passende CSV-Datei gefunden.")
    print()
    print("Gesuchte Speicherorte:")

    for csv_path in POSSIBLE_CSV_PATHS:
        print(f"  - {csv_path}")

    return None


# ---------------------------------------------------------
# 3. Trennzeichen erkennen
# ---------------------------------------------------------

def detect_delimiter(csv_path):
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(4096)

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        return dialect.delimiter
    except csv.Error:
        return ","


# ---------------------------------------------------------
# 4. Passende Spalte suchen
# ---------------------------------------------------------

def find_column(fieldnames, possible_names):
    normalized_columns = {
        column.strip().lower(): column
        for column in fieldnames
        if column is not None
    }

    for name in possible_names:
        normalized_name = name.strip().lower()

        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]

    return None


# ---------------------------------------------------------
# 5. Zahlen sicher umwandeln
# ---------------------------------------------------------

def convert_to_float(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None


# ---------------------------------------------------------
# 6. CSV-Daten einlesen
# ---------------------------------------------------------

def load_route_data(csv_path):
    delimiter = detect_delimiter(csv_path)

    latitude_names = [
        "latitude",
        "lat",
        "breitengrad",
        "gps_latitude",
        "position_lat",
        "position_latitude",
    ]

    longitude_names = [
        "longitude",
        "lon",
        "lng",
        "long",
        "laengengrad",
        "längengrad",
        "gps_longitude",
        "position_lon",
        "position_longitude",
    ]

    elevation_names = [
    "elevation",
    "elev",
    "ele",
    "altitude",
    "alt",
    "hoehe",
    "höhe",
    "gps_elevation",
    ]

    time_names = [
        "time",
        "timestamp",
        "datetime",
        "date_time",
        "zeit",
    ]

    temperature_names = [
        "temperature",
        "temp",
        "temperatur",
    ]

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=delimiter)

        if reader.fieldnames is None:
            print("Fehler: Die CSV-Datei enthält keine Spaltenüberschriften.")
            return None

        latitude_column = find_column(reader.fieldnames, latitude_names)
        longitude_column = find_column(reader.fieldnames, longitude_names)
        elevation_column = find_column(reader.fieldnames, elevation_names)
        time_column = find_column(reader.fieldnames, time_names)
        temperature_column = find_column(
            reader.fieldnames,
            temperature_names
        )

        print(f"Vorhandene Spalten: {reader.fieldnames}")

        if latitude_column is None:
            print("Fehler: Keine passende Breitengrad-Spalte gefunden.")
            print(f"Gesuchte Namen: {latitude_names}")
            return None

        if longitude_column is None:
            print("Fehler: Keine passende Längengrad-Spalte gefunden.")
            print(f"Gesuchte Namen: {longitude_names}")
            return None

        print(f"Breitengrad-Spalte erkannt: {latitude_column}")
        print(f"Längengrad-Spalte erkannt: {longitude_column}")

        if elevation_column is not None:
            print(f"Höhen-Spalte erkannt: {elevation_column}")
        else:
            print("Keine Höhen-Spalte erkannt. Höhe wird auf 0 gesetzt.")

        route_data = []

        for row in reader:
            latitude = convert_to_float(row.get(latitude_column))
            longitude = convert_to_float(row.get(longitude_column))

            if latitude is None or longitude is None:
                continue

            if elevation_column is not None:
                elevation = convert_to_float(row.get(elevation_column))
            else:
                elevation = 0.0

            if elevation is None:
                elevation = 0.0

            time_value = ""
            if time_column is not None:
                time_value = str(row.get(time_column, "")).strip()

            temperature = None
            if temperature_column is not None:
                temperature = convert_to_float(
                    row.get(temperature_column)
                )

            route_data.append(
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "elevation": elevation,
                    "time": time_value,
                    "temperature": temperature,
                }
            )

    if len(route_data) < 2:
        print("Fehler: Es wurden nicht genügend gültige GPS-Punkte gefunden.")
        return None

    return route_data


# ---------------------------------------------------------
# 7. GPS-Koordinaten in Meter umrechnen
# ---------------------------------------------------------

def add_local_coordinates(route_data):
    reference_latitude = route_data[0]["latitude"]
    reference_longitude = route_data[0]["longitude"]

    earth_radius = 6_371_000.0
    reference_latitude_radians = math.radians(reference_latitude)

    for point in route_data:
        latitude_difference = math.radians(
            point["latitude"] - reference_latitude
        )

        longitude_difference = math.radians(
            point["longitude"] - reference_longitude
        )

        north_position = earth_radius * latitude_difference

        east_position = (
            earth_radius
            * longitude_difference
            * math.cos(reference_latitude_radians)
        )

        point["east"] = east_position
        point["north"] = north_position


# ---------------------------------------------------------
# 8. HTML-Datei erstellen
# ---------------------------------------------------------

def create_html(route_data, output_file):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    latitude_values = [
        point["latitude"]
        for point in route_data
    ]

    longitude_values = [
        point["longitude"]
        for point in route_data
    ]

    elevation_values = [
        point["elevation"]
        for point in route_data
    ]

    east_values = [
        point["east"]
        for point in route_data
    ]

    north_values = [
        point["north"]
        for point in route_data
    ]

    minimum_elevation = min(elevation_values)
    maximum_elevation = max(elevation_values)
    elevation_difference = maximum_elevation - minimum_elevation

    # Überhöhung für bessere Sichtbarkeit der Höhenunterschiede
    vertical_exaggeration = 5

    display_elevation_values = [
        (elevation - minimum_elevation) * vertical_exaggeration
        for elevation in elevation_values
    ]

    hover_texts = []

    for index, point in enumerate(route_data, start=1):
        text = (
            f"Punkt: {index}<br>"
            f"Breitengrad: {point['latitude']:.6f}<br>"
            f"Längengrad: {point['longitude']:.6f}<br>"
            f"Höhe: {point['elevation']:.2f} m"
        )

        if point["time"]:
            text += f"<br>Zeit: {point['time']}"

        if point["temperature"] is not None:
            text += (
                f"<br>Temperatur: "
                f"{point['temperature']:.1f} °C"
            )

        hover_texts.append(text)

    center_latitude = sum(latitude_values) / len(latitude_values)
    center_longitude = sum(longitude_values) / len(longitude_values)

    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Interaktive GPS-Route</title>

    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>

    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    >

    <script
        src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
    </script>

    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
        }}

        h1 {{
            text-align: center;
            margin: 15px 0 5px 0;
        }}

        .info {{
            text-align: center;
            margin-bottom: 15px;
            line-height: 1.6;
        }}

        .container {{
            width: 95%;
            max-width: 1400px;
            margin: auto;
        }}

        #map {{
            width: 100%;
            height: 500px;
            border: 1px solid #999;
            border-radius: 8px;
        }}

        #route3d {{
            width: 100%;
            height: 650px;
            margin-top: 20px;
            border: 1px solid #999;
            border-radius: 8px;
            background-color: white;
        }}

        .controls {{
            text-align: center;
            margin: 15px 0;
        }}

        button {{
            padding: 10px 18px;
            margin: 5px;
            font-size: 16px;
            cursor: pointer;
        }}

        .compass {{
            position: absolute;
            top: 80px;
            right: 25px;
            z-index: 1000;
            width: 100px;
            height: 100px;
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid black;
            border-radius: 50%;
            font-weight: bold;
            pointer-events: none;
        }}

        .north {{
            position: absolute;
            top: 5px;
            left: 43px;
        }}

        .south {{
            position: absolute;
            bottom: 5px;
            left: 43px;
        }}

        .east {{
            position: absolute;
            right: 8px;
            top: 40px;
        }}

        .west {{
            position: absolute;
            left: 8px;
            top: 40px;
        }}

        .arrow {{
            position: absolute;
            top: 23px;
            left: 43px;
            width: 0;
            height: 0;
            border-left: 7px solid transparent;
            border-right: 7px solid transparent;
            border-bottom: 28px solid red;
        }}

        .map-wrapper {{
            position: relative;
        }}
    </style>
</head>

<body>
    <div class="container">
        <h1>Interaktive GPS-Route</h1>

        <div class="info">
            GPS-Punkte: {len(route_data)}<br>
            Minimale Höhe: {minimum_elevation:.2f} m |
            Maximale Höhe: {maximum_elevation:.2f} m |
            Höhenunterschied: {elevation_difference:.2f} m<br>
            3D-Darstellung: {vertical_exaggeration}× vertikal überhöht
        </div>

        <div class="map-wrapper">
            <div id="map"></div>

            <div class="compass">
                <div class="north">N</div>
                <div class="south">S</div>
                <div class="east">O</div>
                <div class="west">W</div>
                <div class="arrow"></div>
            </div>
        </div>

        <div class="controls">
            <button onclick="startAnimation()">
                Animation starten
            </button>

            <button onclick="stopAnimation()">
                Animation stoppen
            </button>

            <button onclick="resetAnimation()">
                Zurücksetzen
            </button>
        </div>

        <div id="route3d"></div>
    </div>

    <script>
        const latitudes = {json.dumps(latitude_values)};
        const longitudes = {json.dumps(longitude_values)};
        const elevations = {json.dumps(elevation_values)};
        const displayElevations = {json.dumps(display_elevation_values)};
        const eastValues = {json.dumps(east_values)};
        const northValues = {json.dumps(north_values)};
        const hoverTexts = {json.dumps(hover_texts)};
        const verticalExaggeration = {vertical_exaggeration};

        const map = L.map("map").setView(
            [{center_latitude}, {center_longitude}],
            14
        );

        L.tileLayer(
            "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
            {{
                maxZoom: 19,
                attribution: "&copy; OpenStreetMap"
            }}
        ).addTo(map);

        const routeCoordinates = latitudes.map(
            (latitude, index) => [
                latitude,
                longitudes[index]
            ]
        );

        const routeLine = L.polyline(
            routeCoordinates,
            {{
                weight: 5
            }}
        ).addTo(map);

        map.fitBounds(routeLine.getBounds());

        L.marker(routeCoordinates[0])
            .addTo(map)
            .bindPopup("Startpunkt");

        L.marker(routeCoordinates[routeCoordinates.length - 1])
            .addTo(map)
            .bindPopup("Endpunkt");

        const animatedMapMarker = L.circleMarker(
            routeCoordinates[0],
            {{
                radius: 9,
                weight: 3,
                fillOpacity: 1
            }}
        ).addTo(map);

        const routeTrace = {{
            type: "scatter3d",
            mode: "lines",
            x: eastValues,
            y: northValues,
            z: displayElevations,
            text: hoverTexts,
            hoverinfo: "text",
            line: {{
                width: 8,
                color: elevations,
                colorscale: "Viridis",
                colorbar: {{
                    title: "Höhe [m]"
                }}
            }},
            name: "GPS-Route"
        }};

        const startTrace = {{
            type: "scatter3d",
            mode: "markers+text",
            x: [eastValues[0]],
            y: [northValues[0]],
            z: [displayElevations[0]],
            text: ["Start"],
            textposition: "top center",
            marker: {{
                size: 7
            }},
            name: "Startpunkt"
        }};

        const endIndex = eastValues.length - 1;

        const endTrace = {{
            type: "scatter3d",
            mode: "markers+text",
            x: [eastValues[endIndex]],
            y: [northValues[endIndex]],
            z: [displayElevations[endIndex]],
            text: ["Ende"],
            textposition: "top center",
            marker: {{
                size: 7
            }},
            name: "Endpunkt"
        }};

        const animatedTrace = {{
            type: "scatter3d",
            mode: "markers",
            x: [eastValues[0]],
            y: [northValues[0]],
            z: [displayElevations[0]],
            marker: {{
                size: 9
            }},
            name: "Aktuelle Position"
        }};

        const layout = {{
            title: "Interaktive 3D-Darstellung der Route",

            scene: {{
                xaxis: {{
                    title: "Westen ← Entfernung Ost [m] → Osten"
                }},

                yaxis: {{
                    title: "Süden ← Entfernung Nord [m] → Norden"
                }},

                zaxis: {{
                    title: "Höhenunterschied, " +
                           verticalExaggeration +
                           "× überhöht"
                }},

                aspectmode: "manual",

                aspectratio: {{
                    x: 1.5,
                    y: 1.5,
                    z: 0.8
                }},

                camera: {{
                    eye: {{
                        x: 1.5,
                        y: 1.5,
                        z: 1.0
                    }}
                }}
            }},

            margin: {{
                l: 0,
                r: 0,
                b: 0,
                t: 50
            }},

            legend: {{
                x: 0,
                y: 1
            }}
        }};

        Plotly.newPlot(
            "route3d",
            [
                routeTrace,
                startTrace,
                endTrace,
                animatedTrace
            ],
            layout,
            {{
                responsive: true
            }}
        );

        let animationIndex = 0;
        let animationTimer = null;

        function updateAnimatedPosition() {{
            if (animationIndex >= latitudes.length) {{
                stopAnimation();
                return;
            }}

            animatedMapMarker.setLatLng([
                latitudes[animationIndex],
                longitudes[animationIndex]
            ]);

            Plotly.restyle(
                "route3d",
                {{
                    x: [[eastValues[animationIndex]]],
                    y: [[northValues[animationIndex]]],
                    z: [[displayElevations[animationIndex]]]
                }},
                [3]
            );

            animationIndex += 1;
        }}

        function startAnimation() {{
            if (animationTimer !== null) {{
                return;
            }}

            animationTimer = setInterval(
                updateAnimatedPosition,
                100
            );
        }}

        function stopAnimation() {{
            if (animationTimer !== null) {{
                clearInterval(animationTimer);
                animationTimer = null;
            }}
        }}

        function resetAnimation() {{
            stopAnimation();

            animationIndex = 0;

            animatedMapMarker.setLatLng([
                latitudes[0],
                longitudes[0]
            ]);

            Plotly.restyle(
                "route3d",
                {{
                    x: [[eastValues[0]]],
                    y: [[northValues[0]]],
                    z: [[displayElevations[0]]]
                }},
                [3]
            );
        }}
    </script>
</body>
</html>
"""

    output_file.write_text(html_content, encoding="utf-8")


# ---------------------------------------------------------
# 9. Hauptprogramm
# ---------------------------------------------------------

def main():
    print("Interaktive GPS-Karte wird erstellt.")
    print()

    csv_path = find_csv_file()

    if csv_path is None:
        return

    print(f"CSV-Datei gefunden: {csv_path}")
    print()

    route_data = load_route_data(csv_path)

    if route_data is None:
        print()
        print("Die interaktive 3D-Route konnte nicht erstellt werden.")
        return

    add_local_coordinates(route_data)

    elevation_values = [point["elevation"] for point in route_data]

    print()
    print(f"Anzahl gültiger GPS-Punkte: {len(route_data)}")
    print(f"Minimale Höhe: {min(elevation_values):.2f} m")
    print(f"Maximale Höhe: {max(elevation_values):.2f} m")
    print(
        "Höhenunterschied: "
        f"{max(elevation_values) - min(elevation_values):.2f} m"
    )

    create_html(route_data, OUTPUT_FILE)

    print()
    print("Die interaktive 3D-Route wurde erfolgreich erstellt.")
    print(f"HTML-Datei: {OUTPUT_FILE}")

    try:
        webbrowser.open(OUTPUT_FILE.as_uri())
    except Exception:
        print("Die HTML-Datei konnte nicht automatisch geöffnet werden.")
        print("Öffne sie manuell im Browser.")


if __name__ == "__main__":
    main()
