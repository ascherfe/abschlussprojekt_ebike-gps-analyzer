import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.plots import Plotter

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "src"))

# Sichere Importe aus dem Unterordner src/
from src.data_loader import GPSDataLoader
from src.calculations import PhysicsCalculator
from src.motor import Motor
from src.battery import LiPoBattery, NMCBattery

CSV_PATH = BASE_DIR / "data" / "raw" / "final_project_input_data.csv"


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
    except Exception as e:
        print(f"Hinweis: Konnte Startdaten für Wetter nicht automatisch lesen ({e}). Nutze Standardwerte.")
        real_wind_speed, real_wind_dir = 0.0, 0.0

    # Metriken mit den live gezogenen Wetterdaten berechnen!
    data = calculator.calculate_metrics(data, wind_speed=real_wind_speed, wind_direction=real_wind_dir)

    # 3. Hilfsspalte für die x-Achse & Distanzen berechnen
    data['elapsed_time'] = data['delta_t'].cumsum()
    data["distance"] = data["distance_delta"].cumsum()

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
    motor = Motor(
        wheel_diameter_inch=27,
        motor_constant=4.5
    )

    lipo = LiPoBattery(
        cells_series=10,
        cells_parallel=3,   
        capacity_ah=12,     
        initial_soc=1.0
    )

    nmc = NMCBattery(
        cells_series=10,
        cells_parallel=3,  
        capacity_ah=16,     
        initial_soc=1.0
    )

    force_column = "force_vortrieb"
    velocity_column = "speed"
    time_column = "elapsed_time"

    results = []

    # Simulationsschleife über den gesamten Fahrtverlauf
    for i in range(1, len(data)):
        force = data[force_column].iloc[i]
        velocity = data[velocity_column].iloc[i]
        dt = data['delta_t'].iloc[i]

        # Berechnungen des Antriebsstrangs ausführen
        raw_power = motor.calculate_power(force, velocity)
        torque = motor.calculate_torque(force)
        current = motor.calculate_motor_current(torque)

        # Leistung & Strom auf E-Bike-Realismus begrenzen (max 500W)
        MAX_MOTOR_POWER = 500.0  # Watt
        if raw_power > MAX_MOTOR_POWER:
            power = MAX_MOTOR_POWER
            if velocity > 0:
                current = min(current, power / (lipo.get_terminal_voltage(current) + 0.1))
        else:
            power = raw_power

        # Akku-Simulation: Nur entladen, wenn noch Ladung da ist
        if lipo.discharge(0, 0) > 0:  
            soc_lipo = lipo.discharge(current, dt)
        else:
            soc_lipo = 0.0

        if nmc.discharge(0, 0) > 0:
            soc_nmc = nmc.discharge(current, dt)
        else:
            soc_nmc = 0.0

        # Spannung abfragen
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

    # Ergebnisse in DataFrame
    results_df = pd.DataFrame(results)

    # Berechnete Daten strukturiert abspeichern
    output_path = BASE_DIR / "data" / "processed" / "simulation_results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)

    print("\n--- Simulation erfolgreich abgeschlossen ---")
    print(f"Ergebnisse gespeichert unter: {output_path}")

    # Aggregierte Kennzahlen im Terminal ausgeben
    print(f"Zurückgelegte Gesamtstrecke: {data['distance_delta'].sum() / 1000:.2f} km")
    print(f"Gesamte Fahrtzeit:          {hours:02d}:{minutes:02d}:{seconds:02d} (hh:mm:ss)")
    print(f"Kumulierter Anstieg (↑):    {total_ascent:.1f} m")
    print(f"Kumulierter Abstieg (↓):    {abs(total_descent):.1f} m")
    print(f"Maximale Motorleistung:     {results_df['power'].max():.2f} W")
    print(f"Durchschnittsgeschwindigkeit: {results_df['velocity'].mean() * 3.6:.2f} km/h")

    # Diagramme generieren
    plot_results(results_df, data)


def plot_results(results, data):
    plt.figure()
    plt.plot(results["time"], results["velocity"] * 3.6, color="blue")
    plt.xlabel("Zeit / s")
    plt.ylabel("Geschwindigkeit / km/h")
    plt.title("Geschwindigkeit über die Zeit")
    plt.grid(True)

    plt.figure()
    plt.plot(results["time"], Antiquated_power := results["power"], color="orange")
    plt.xlabel("Zeit / s")
    plt.ylabel("Leistung / W")
    plt.title("Benötigte Motorleistung über die Zeit")
    plt.grid(True)

    plt.figure()
    # Der LiPo wird dicker gezeichnet, der NMC leicht gestrichelt darübergelegt, um optische Unterschiede hervorzuheben
    plt.plot(results["time"], results["soc_lipo"] * 100, label="LiPo (12 Ah)", color="red", linewidth=2.5)
    plt.plot(results["time"], results["soc_nmc"] * 100, label="NMC (16 Ah)", color="green", linestyle="--", linewidth=2)
    plt.xlabel("Zeit / s")
    plt.ylabel("Ladezustand (SOC) / %")
    plt.title("Akkuladestand im Vergleich")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(results["time"], results["motor_current"], color="purple")
    plt.xlabel("Zeit / s")
    plt.ylabel("Motorstrom / A")
    plt.title("Motorstrom über die Zeit")
    plt.grid(True)
    
    plt.show()

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


if __name__ == "__main__":
    main()