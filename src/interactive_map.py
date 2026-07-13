from pathlib import Path
import csv
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

CSV_PATH = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "final_project_input_data.csv"
)

OUTPUT_PATH = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "route_3d_wind_farbcodiert.png"
)


def load_gps_data(csv_path):
    latitude_values = []
    longitude_values = []
    elevation_values = []

    with csv_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            latitude = float(row["lat"])
            longitude = float(row["lon"])
            elevation = float(row["ele"])

            latitude_values.append(latitude)
            longitude_values.append(longitude)
            elevation_values.append(elevation)

    return latitude_values, longitude_values, elevation_values


def convert_to_local_coordinates(
    latitude_values,
    longitude_values
):
    earth_radius = 6_371_000

    reference_latitude = latitude_values[0]
    reference_longitude = longitude_values[0]

    reference_latitude_rad = math.radians(
        reference_latitude
    )

    east_values = []
    north_values = []

    for latitude, longitude in zip(
        latitude_values,
        longitude_values
    ):
        latitude_difference = math.radians(
            latitude - reference_latitude
        )

        longitude_difference = math.radians(
            longitude - reference_longitude
        )

        north = earth_radius * latitude_difference

        east = (
            earth_radius
            * longitude_difference
            * math.cos(reference_latitude_rad)
        )

        east_values.append(east)
        north_values.append(north)

    return east_values, north_values


def calculate_headings_simple(lat_vals, lon_vals):
    """Berechnet die Fahrtrichtungen für die Segmente."""
    headings = [0.0]
    for i in range(1, len(lat_vals)):
        phi1 = math.radians(lat_vals[i-1])
        phi2 = math.radians(lat_vals[i])
        delta_lambda = math.radians(lon_vals[i] - lon_vals[i-1])
        y = math.sin(delta_lambda) * math.cos(phi2)
        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
        heading = math.degrees(math.atan2(y, x))
        headings.append((heading + 360.0) % 360.0)
    return headings


def plot_3d_route_with_wind(
    east_values,
    north_values,
    elevation_values,
    headings,
    real_wind_speed,
    real_wind_dir
):
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    figure = plt.figure(figsize=(11, 8))
    axis = figure.add_subplot(
        111,
        projection="3d"
    )

    x = np.array(east_values)
    y = np.array(north_values)
    z = np.array(elevation_values)
    h = np.array(headings)

    # Physikalische Windbelastung für jedes Wegsegment berechnen
    angle_diff = np.radians(h - real_wind_dir)
    wind_impact = (real_wind_speed * np.cos(angle_diff)) * 3.6

    # 3D Segmente bauen
    points = np.array([x, y, z]).T.reshape(-1, 1, 3)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Farbkarte laden (Grün = Rückenwind, Rot = Gegenwind)
    cmap = plt.get_cmap('RdYlGn_r')
    
    lc = Line3DCollection(segments, cmap=cmap, linewidths=3.5)
    lc.set_array(wind_impact[:-1])
    line = axis.add_collection3d(lc)

    # Start- und Endpunkte markieren
    axis.scatter(x[0], y[0], z[0], color="blue", s=50, label="Start", zorder=5)
    axis.scatter(x[-1], y[-1], z[-1], color="orange", s=50, label="Ende", zorder=5)

    axis.set_xlim(x.min(), x.max())
    axis.set_ylim(y.min(), y.max())
    axis.set_zlim(z.min(), z.max())

    axis.set_title("3D-Streckenprofil mit farbkodiertem Windeinfluss", fontweight='bold', pad=20)
    axis.set_xlabel("Westen ← Entfernung Ost [m] → Osten")
    axis.set_ylabel("Süden ← Entfernung Nord [m] → Norden")
    axis.set_zlabel("Höhe [m]")
    axis.legend()

    # Legenden-Farbbalken hinzufügen
    cbar = figure.colorbar(line, ax=axis, pad=0.1, shrink=0.55)
    cbar.set_label("Effektive Windkomponente / km/h (Rot = Gegenwind)")

    plt.tight_layout()
    plt.savefig(
        OUTPUT_PATH,
        dpi=300
    )
    plt.show()


def main():
    if not CSV_PATH.exists():
        print("CSV-Datei wurde nicht gefunden:")
        print(CSV_PATH)
        return

    latitude_values, longitude_values, elevation_values = (
        load_gps_data(CSV_PATH)
    )

    east_values, north_values = (
        convert_to_local_coordinates(
            latitude_values,
            longitude_values
        )
    )

    headings = calculate_headings_simple(latitude_values, longitude_values)

    # Statische Beispiel-Werte für den Wind (wird an die echten API-Werte angepasst)
    real_wind_speed = 4.2  # m/s
    real_wind_dir = 270.0  # Grad (Westwind)

    print(f"Anzahl GPS-Punkte: {len(latitude_values)}")
    print("Generiere farbkodierte Wind-3D-Map...")

    plot_3d_route_with_wind(
        east_values,
        north_values,
        elevation_values,
        headings,
        real_wind_speed,
        real_wind_dir
    )


if __name__ == "__main__":
    main()