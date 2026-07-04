from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from motor import Motor
from battery import LiPoBattery, NMCBattery


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "raw" / "final_project_input_data.csv"


def main():
    data = pd.read_csv(CSV_PATH)

    print("CSV erfolgreich eingelesen:")
    print(data.head())

    motor = Motor(
        wheel_diameter_inch=27,
        motor_constant=1.5
    )

    lipo = LiPoBattery(
        cells_series=10,
        cells_parallel=1,
        capacity_ah=10,
        initial_soc=1.0
    )

    nmc = NMCBattery(
        cells_series=10,
        cells_parallel=1,
        capacity_ah=10,
        initial_soc=1.0
    )

    # anpassen an Felix's Bezeichnungen!
    force_column = "force"
    velocity_column = "velocity"
    time_column = "time"

    results = []

    for i in range(1, len(data)):
        force = data[force_column].iloc[i]
        velocity = data[velocity_column].iloc[i]

        dt = data[time_column].iloc[i] - data[time_column].iloc[i - 1]

        power = motor.calculate_power(force, velocity)
        torque = motor.calculate_torque(force)
        current = motor.calculate_motor_current(torque)

        soc_lipo = lipo.discharge(current, dt)
        soc_nmc = nmc.discharge(current, dt)

        voltage_lipo = lipo.get_terminal_voltage(current)
        voltage_nmc = nmc.get_terminal_voltage(current)

        results.append({
            "time": data[time_column].iloc[i],
            "force": force,
            "velocity": velocity,
            "power": power,
            "torque": torque,
            "motor_current": current,
            "soc_lipo": soc_lipo,
            "soc_nmc": soc_nmc,
            "voltage_lipo": voltage_lipo,
            "voltage_nmc": voltage_nmc
        })

    results_df = pd.DataFrame(results)

    output_path = BASE_DIR / "data" / "processed" / "simulation_results.csv"
    results_df.to_csv(output_path, index=False)

    print("Simulation abgeschlossen.")
    print(f"Ergebnisse gespeichert unter: {output_path}")

    plot_results(results_df)


def plot_results(results):
    plt.figure()
    plt.plot(results["time"], results["velocity"])
    plt.xlabel("Zeit / s")
    plt.ylabel("Geschwindigkeit / m/s")
    plt.title("Geschwindigkeit über die Zeit")
    plt.grid()
    plt.show()

    plt.figure()
    plt.plot(results["time"], results["power"])
    plt.xlabel("Zeit / s")
    plt.ylabel("Leistung / W")
    plt.title("Leistung über die Zeit")
    plt.grid()
    plt.show()

    plt.figure()
    plt.plot(results["time"], results["soc_lipo"] * 100, label="LiPo")
    plt.plot(results["time"], results["soc_nmc"] * 100, label="NMC")
    plt.xlabel("Zeit / s")
    plt.ylabel("Ladezustand / %")
    plt.title("Akkuladestand über die Zeit")
    plt.legend()
    plt.grid()
    plt.show()

    plt.figure()
    plt.plot(results["time"], results["motor_current"])
    plt.xlabel("Zeit / s")
    plt.ylabel("Motorstrom / A")
    plt.title("Motorstrom über die Zeit")
    plt.grid()
    plt.show()


if __name__ == "__main__":
    main()