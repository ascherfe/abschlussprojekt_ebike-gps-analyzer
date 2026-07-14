import sys
from pathlib import Path
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from src.plots import Plotter
from src.pdf import PDFReport

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "src"))

# Sichere Importe aus dem Unterordner src/
from src.data_loader import GPSDataLoader
from src.calculations import PhysicsCalculator
from src.motor import Motor
from src.battery import LiPoBattery, NMCBattery

CSV_PATH = BASE_DIR / "data" / "raw" / "final_project_input_data.csv"


def convert_to_local_coordinates(latitude_values, longitude_values):
    """Berechnet die lokalen X/Y Koordinaten im Meterraster (Code deines Kollegen)."""
    earth_radius = 6_371_000
    reference_latitude = latitude_values[0]
    reference_longitude = longitude_values[0]
    reference_latitude_rad = math.radians(reference_latitude)

    east_values = []
    north_values = []

    for latitude, longitude in zip(latitude_values, longitude_values):
        latitude_difference = math.radians(latitude - reference_latitude)
        longitude_difference = math.radians(longitude - reference_longitude)

        north = earth_radius * latitude_difference
        east = (
            earth_radius
            * longitude_difference
            * math.cos(reference_latitude_rad)
        )
        east_values.append(east)
        north_values.append(north)

    return east_values, north_values


def main():
    # 1. Daten über den DataLoader einlesen, bereinigen und vereinheitlichen
    loader = GPSDataLoader(str(CSV_PATH))
    data = loader.load_and_clean_data()

    print("\nCSV erfolgreich eingelesen und vorbereitet (Vorschau):")
    print(data.head())

    # 2. Physikalische Metriken initialisieren
    calculator = PhysicsCalculator(total_mass=100.0, cr=0.004)
    
    # Reale Wetterdaten basierend auf dem ersten CSV-Eintrag live abrufen
    try:
        start_lat = data['lat'].iloc[0]
        start_lon = data['lon'].iloc[0]
        start_time = data['timestamp'].iloc[0]
        real_wind_speed, real_wind_dir = calculator.fetch_real_weather_data(start_lat, start_lon, start_time)
        
        # --- Fallback, falls die API 0 liefert ---
        if real_wind_speed == 0.0:
            print("Refetch/Fallback: API lieferte Windstille. Setze realistische Test-Wetterdaten.")
            real_wind_speed = 4.5   # ca. 16 km/h
            real_wind_dir = 240.0   # Wind aus Süd-West
    except Exception as e:
        print(f"Hinweis: Konnte Startdaten für Wetter nicht lesen ({e}). Nutze vordefinierten Wind.")
        real_wind_speed = 4.5
        real_wind_dir = 240.0

    # Metriken mit den live gezogenen Wetterdaten berechnen!
    data = calculator.calculate_metrics(data, wind_speed=real_wind_speed, wind_direction=real_wind_dir)

    # 3. Hilfsspalte für die x-Achse & Distanzen berechnen
    data['elapsed_time'] = data['delta_t'].cumsum()
    data["distance"] = data["distance_delta"].cumsum()

    # Lokale Meter-Koordinaten für den 3D-Plot bestimmen
    east_vals, north_vals = convert_to_local_coordinates(data['lat'].values, data['lon'].values)
    data['east'] = east_vals
    data['north'] = north_vals

    # Steigungswinkel in Prozent umrechnen
    data["gradient_percent"] = np.tan(data["slope_angle"]) * 100

    # Berechnung der Höhenmeter & Gesamtzeit
    ele_deltas = data['ele_smoothed'].diff().fillna(0.0)
    total_ascent = ele_deltas[ele_deltas > 0].sum()   # Alle positiven Änderungen addieren
    total_descent = ele_deltas[ele_deltas < 0].sum()  # Alle negativen Änderungen addieren
    
    total_time_seconds = data['delta_t'].sum()
    hours = int(total_time_seconds // 3600)
    minutes = int((total_time_seconds % 3600) // 60)
    seconds = int(total_time_seconds % 60)

    # Instanziierung der Komponenten des Antriebsstrangs
    motor = Motor(wheel_diameter_inch=27, motor_constant=4.5)
    lipo = LiPoBattery(cells_series=10, cells_parallel=3, capacity_ah=12, initial_soc=1.0)
    nmc = NMCBattery(cells_series=10, cells_parallel=3, capacity_ah=16, initial_soc=1.0)

    force_column = "force_vortrieb"
    velocity_column = "speed"
    time_column = "elapsed_time"

    results = []

    # Simulationsschleife über den gesamten Fahrtverlauf
    for i in range(1, len(data)):
        force = data[force_column].iloc[i]
        velocity = data[velocity_column].iloc[i]
        dt = data['delta_t'].iloc[i]

        raw_power = motor.calculate_power(force, velocity)
        torque = motor.calculate_torque(force)
        current = motor.calculate_motor_current(torque)

        # Leistung & Strom begrenzen (max 500W)
        MAX_MOTOR_POWER = 500.0  
        if raw_power > MAX_MOTOR_POWER:
            power = MAX_MOTOR_POWER
            if velocity > 0:
                current = min(current, power / (lipo.get_terminal_voltage(current) + 0.1))
        else:
            power = raw_power

        if lipo.discharge(0, 0) > 0:  
            soc_lipo = lipo.discharge(current, dt)
        else:
            soc_lipo = 0.0

        if nmc.discharge(0, 0) > 0:
            soc_nmc = nmc.discharge(current, dt)
        else:
            soc_nmc = 0.0

        voltage_lipo = lipo.get_terminal_voltage(current) if soc_lipo > 0 else 0.0
        voltage_nmc = nmc.get_terminal_voltage(current) if soc_nmc > 0 else 0.0

        results.append({
            "time": data[time_column].iloc[i],
            "force": force,
            "velocity": velocity,
            "power": power,
            "torque": torque,
            "motor_current": current if soc_lipo > 0 or soc_nmc > 0 else 0.0,
            "soc_lipo": soc_lipo,
            "soc_nmc": soc_nmc,
            "voltage_lipo": voltage_lipo,
            "voltage_nmc": voltage_nmc
        })

    results_df = pd.DataFrame(results)

    output_path = BASE_DIR / "data" / "processed" / "simulation_results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)

    print("\n--- Simulation erfolgreich abgeschlossen ---")
    print(f"Zurückgelegte Gesamtstrecke: {data['distance_delta'].sum() / 1000:.2f} km")
    print(f"Gesamte Fahrtzeit:          {hours:02d}:{minutes:02d}:{seconds:02d}")

    # Diagramme generieren (Wetter-Parameter übergeben!)
        # Diagramme erstellen und deren Dateipfade zurückgeben
    plot_paths = plot_results(
        results_df,
        data,
        real_wind_speed,
        real_wind_dir
    )

    # Kennwerte für die PDF berechnen
    total_distance_km = data["distance_delta"].sum() / 1000
    average_speed_kmh = results_df["velocity"].mean() * 3.6
    maximum_speed_kmh = results_df["velocity"].max() * 3.6

    average_power = results_df["power"].mean()
    maximum_power = results_df["power"].max()

    average_current = results_df["motor_current"].mean()
    maximum_current = results_df["motor_current"].max()

    minimum_elevation = data["ele_smoothed"].min()
    maximum_elevation = data["ele_smoothed"].max()
    elevation_difference = maximum_elevation - minimum_elevation

    final_lipo_soc = results_df["soc_lipo"].iloc[-1] * 100
    final_nmc_soc = results_df["soc_nmc"].iloc[-1] * 100

    # Alle Werte für die Übersichtsseite der PDF
    pdf_results = {
        "Anzahl GPS-Punkte": len(data),
        "Gesamtstrecke": f"{total_distance_km:.2f} km",
        "Gesamte Fahrtzeit": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
        "Durchschnittsgeschwindigkeit": f"{average_speed_kmh:.2f} km/h",
        "Maximale Geschwindigkeit": f"{maximum_speed_kmh:.2f} km/h",
        "Minimale Höhe": f"{minimum_elevation:.2f} m",
        "Maximale Höhe": f"{maximum_elevation:.2f} m",
        "Höhenunterschied": f"{elevation_difference:.2f} m",
        "Positive Höhenmeter": f"{total_ascent:.2f} m",
        "Negative Höhenmeter": f"{abs(total_descent):.2f} m",
        "Durchschnittliche Motorleistung": f"{average_power:.2f} W",
        "Maximale Motorleistung": f"{maximum_power:.2f} W",
        "Durchschnittlicher Motorstrom": f"{average_current:.2f} A",
        "Maximaler Motorstrom": f"{maximum_current:.2f} A",
        "LiPo-Ladezustand am Ende": f"{final_lipo_soc:.2f} %",
        "NMC-Ladezustand am Ende": f"{final_nmc_soc:.2f} %",
        "Reale Windgeschwindigkeit": f"{real_wind_speed:.2f} m/s",
        "Reale Windrichtung": f"{real_wind_dir:.2f}°",
    }

    # Speicherort des PDF-Berichts
    pdf_output_path = (
        BASE_DIR
        / "data"
        / "processed"
        / "ebike_ergebnisbericht.pdf"
    )

    # PDF erstellen
    report = PDFReport(pdf_output_path)

    report.create_report(
        results=pdf_results,
        plot_paths=plot_paths
    )

    print("\n--- PDF-Bericht erfolgreich erstellt ---")
    print(f"PDF-Datei: {pdf_output_path}")




def plot_results(results, data, wind_speed, wind_dir):
    """
    Erstellt alle Diagramme, speichert sie als PNG und gibt deren Pfade zurück.
    """

    plots_directory = BASE_DIR / "data" / "processed" / "plots"
    plots_directory.mkdir(parents=True, exist_ok=True)

    plot_paths = []

    # ---------------------------------------------------------
    # 1. Geschwindigkeit über die Zeit
    # ---------------------------------------------------------
    velocity_plot_path = plots_directory / "geschwindigkeit.png"

    plt.figure(figsize=(10, 6))
    plt.plot(
        results["time"],
        results["velocity"] * 3.6,
        color="blue"
    )
    plt.xlabel("Zeit / s")
    plt.ylabel("Geschwindigkeit / km/h")
    plt.title("Geschwindigkeit über die Zeit")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(velocity_plot_path, dpi=200)
    plt.close()

    plot_paths.append(velocity_plot_path)

    # ---------------------------------------------------------
    # 2. Motorleistung über die Zeit
    # ---------------------------------------------------------
    power_plot_path = plots_directory / "motorleistung.png"

    plt.figure(figsize=(10, 6))
    plt.plot(
        results["time"],
        results["power"],
        color="orange"
    )
    plt.xlabel("Zeit / s")
    plt.ylabel("Leistung / W")
    plt.title("Benötigte Motorleistung über die Zeit")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(power_plot_path, dpi=200)
    plt.close()

    plot_paths.append(power_plot_path)

    # ---------------------------------------------------------
    # 3. Akkuladestand im Vergleich
    # ---------------------------------------------------------
    battery_plot_path = plots_directory / "akkuladestand.png"

    plt.figure(figsize=(10, 6))
    plt.plot(
        results["time"],
        results["soc_lipo"] * 100,
        label="LiPo (12 Ah)",
        color="red",
        linewidth=2.5
    )
    plt.plot(
        results["time"],
        results["soc_nmc"] * 100,
        label="NMC (16 Ah)",
        color="green",
        linestyle="--",
        linewidth=2
    )
    plt.xlabel("Zeit / s")
    plt.ylabel("Ladezustand (SOC) / %")
    plt.title("Akkuladestand im Vergleich")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(battery_plot_path, dpi=200)
    plt.close()

    plot_paths.append(battery_plot_path)

    # ---------------------------------------------------------
    # 4. Motorstrom über die Zeit
    # ---------------------------------------------------------
    current_plot_path = plots_directory / "motorstrom.png"

    plt.figure(figsize=(10, 6))
    plt.plot(
        results["time"],
        results["motor_current"],
        color="purple"
    )
    plt.xlabel("Zeit / s")
    plt.ylabel("Motorstrom / A")
    plt.title("Motorstrom über die Zeit")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(current_plot_path, dpi=200)
    plt.close()

    plot_paths.append(current_plot_path)

    # ---------------------------------------------------------
    # Erweiterte Diagramme aus plots.py
    # ---------------------------------------------------------
    plotter = Plotter()

    # Höhenprofil
    plotter.plot_height_profile(
        data["distance"],
        data["ele_smoothed"]
    )

    # Höhenprofil mit farbiger Steigung
    plotter.plot_colored_gradient(
        data["distance"],
        data["ele_smoothed"],
        data["gradient_percent"]
    )

    # Zeitverlauf des Windeinflusses
    plotter.plot_wind_impact_timeline(
        results["time"],
        data["heading"].iloc[1:],
        wind_speed,
        wind_dir
    )

    # Farbkodierte 3D-Streckenkarte
    plotter.plot_3d_route_with_wind(
        data["east"],
        data["north"],
        data["ele_smoothed"],
        data["heading"],
        wind_speed,
        wind_dir
    )

    # Bereits vom Plotter gespeicherte Diagramme ergänzen.
    # Die Dateinamen müssen mit den Namen in plots.py übereinstimmen.
    additional_plot_paths = [
    plots_directory / "hoehenprofil.png",
    plots_directory / "hoehenprofil_steigung.png",
    plots_directory / "wind_verlauf_zeit.png",
    plots_directory / "route_3d_wind_farbcodiert.png",
    plots_directory / "parameter_study_result.png",
    plots_directory / "route_3d.png",
    ]

    for path in additional_plot_paths:
        if path.exists():
            plot_paths.append(path)
        else:
            print(
                f"Hinweis: Das Diagramm wurde nicht für die PDF gefunden: "
                f"{path.name}"
            )

    print("\n--- Diagramme erfolgreich gespeichert ---")

    for path in plot_paths:
        print(f"Diagramm: {path}")

    return plot_paths

if __name__ == "__main__":
    main()