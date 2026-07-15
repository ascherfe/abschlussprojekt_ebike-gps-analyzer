import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Verhindert, dass die Plots unter Windows blockieren
import matplotlib
matplotlib.use("TkAgg")

# src-Ordner zum Systempfad hinzufügen, damit die Imports klappen
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "src"))

from src.data_loader import GPSDataLoader
from src.calculations import PhysicsCalculator
from src.motor import Motor
from src.battery import LiPoBattery, NMCBattery

CSV_PATH = BASE_DIR / "data" / "raw" / "final_project_input_data.csv"


def run_simulation_instance(data_raw, total_mass, rolling_resistance, wind_speed, wind_dir):
    """
    Rechnet eine einzelne Simulation mit bestimmten Werten (Masse, Reifenwiderstand)
    durch und gibt den SOC-Verlauf für beide Akkus zurück.
    """
    df = data_raw.copy()
    
    # Fahrphysik mit den aktuellen Parametern berechnen
    calculator = PhysicsCalculator(total_mass=total_mass, cr=rolling_resistance)
    df = calculator.calculate_metrics(df, wind_speed=wind_speed, wind_direction=wind_dir)
    df['elapsed_time'] = df['delta_t'].cumsum()
    
    # Motor und Akkus initialisieren (Motorkonstante 1.5 laut Vorgabe)
    motor = Motor(wheel_diameter_inch=27, motor_constant=1.5)
    lipo = LiPoBattery(cells_series=10, cells_parallel=3, capacity_ah=12, initial_soc=1.0)
    nmc = NMCBattery(cells_series=10, cells_parallel=3, capacity_ah=16, initial_soc=1.0)
    
    lipo_soc_history = [1.0]
    nmc_soc_history = [1.0]
    time_history = [0.0]
    
    # Simulationsschleife über das Fahrprofil
    for i in range(1, len(df)):
        force = df["force_vortrieb"].iloc[i]
        velocity = df["speed"].iloc[i]
        dt = df['delta_t'].iloc[i]
        
        # Leistung und Strom berechnen
        raw_power = motor.calculate_power(force, velocity)
        torque = motor.calculate_torque(force)
        current = motor.calculate_motor_current(torque)
        
        # Leistungslimit einhalten (max. 500W Spitzenleistung)
        if raw_power > 500.0:
            power = 500.0
            if velocity > 0:
                current = min(current, power / (lipo.get_terminal_voltage(current) + 0.1))
        
        # Akkus entladen
        if lipo.discharge(0, 0) > 0:
            soc_lipo = lipo.discharge(current, dt)
        else:
            soc_lipo = 0.0
            
        if nmc.discharge(0, 0) > 0:
            soc_nmc = nmc.discharge(current, dt)
        else:
            soc_nmc = 0.0
            
        lipo_soc_history.append(soc_lipo)
        nmc_soc_history.append(soc_nmc)
        time_history.append(df["elapsed_time"].iloc[i])
        
    return time_history, lipo_soc_history, nmc_soc_history


def main():
    print("--- Starte automatisierte Parameterstudie ---")
    
    # GPS-Daten laden
    loader = GPSDataLoader(str(CSV_PATH))
    raw_data = loader.load_and_clean_data()
    
    # Wetterdaten einmalig für den Startpunkt abrufen
    calc_weather = PhysicsCalculator()
    try:
        w_speed, w_dir = calc_weather.fetch_real_weather_data(
            raw_data['lat'].iloc[0], 
            raw_data['lon'].iloc[0], 
            raw_data['timestamp'].iloc[0]
        )
    except Exception:
        print("Wetter-API konnte nicht geladen werden. Nutze Standardwerte (Windstille).")
        w_speed, w_dir = 0.0, 0.0

    # Szenarien definieren (Massen basieren auf 10kg Bike + Fahrergewicht)
    scenarios = [
        {"mass": 70.0,  "cr": 0.003, "label": "Leicht (70kg, Rennreifen)", "color_lipo": "#ff6666", "color_nmc": "#66ff66"},
        {"mass": 80.0,  "cr": 0.004, "label": "Standard (80kg, Trekking)", "color_lipo": "#cc0000", "color_nmc": "#009900"},
        {"mass": 110.0, "cr": 0.006, "label": "Schwer (110kg, Offroad)",  "color_lipo": "#660000", "color_nmc": "#003300"}
    ]
    
    plt.figure(figsize=(12, 7))
    
    # Jedes Szenario simulieren und direkt in ein Diagramm zeichnen
    for sc in scenarios:
        print(f"\nSimuliere {sc['label']}...")
        times, lipo_socs, nmc_socs = run_simulation_instance(
            raw_data, sc["mass"], sc["cr"], w_speed, w_dir
        )
        
        # Prozentwerte für den Plot berechnen
        lipo_percent = [s * 100 for s in lipo_socs]
        nmc_percent = [s * 100 for s in nmc_socs]
        
        # LiPo durchgezogen, NMC gestrichelt darstellen
        plt.plot(times, lipo_percent, label=f"{sc['label']} - LiPo (12Ah)", color=sc["color_lipo"], linewidth=2)
        plt.plot(times, nmc_percent, label=f"{sc['label']} - NMC (16Ah)", color=sc["color_nmc"], linestyle="--", linewidth=2)
    
    # Plot beschriften und formatieren
    plt.xlabel("Zeit / s", fontsize=12)
    plt.ylabel("Akkuladezustand (SOC) / %", fontsize=12)
    plt.title("Parameterstudie: Einfluss von Gewicht & Reifen auf LiPo vs. NMC", fontsize=14, fontweight='bold')
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=9, loc="lower left")
    
    # Diagramm im plots-Ordner sichern
    output_fig = BASE_DIR / "data" / "processed" / "plots" / "parameter_study_result.png"
    output_fig.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_fig, dpi=300)
    print(f"\n---> Diagramm gespeichert unter: {output_fig}")
    
    plt.show()


if __name__ == "__main__":
    main()