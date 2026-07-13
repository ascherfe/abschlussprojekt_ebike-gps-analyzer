from pathlib import Path
import csv
import math
import matplotlib.pyplot as plt


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
    / "route_3d.png"
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


def plot_3d_route(
    east_values,
    north_values,
    elevation_values
):
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    figure = plt.figure(figsize=(10, 7))

    axis = figure.add_subplot(
        111,
        projection="3d"
    )

    axis.plot(
        east_values,
        north_values,
        elevation_values,
        linewidth=2
    )

    axis.scatter(
        east_values[0],
        north_values[0],
        elevation_values[0],
        label="Start"
    )

    axis.scatter(
        east_values[-1],
        north_values[-1],
        elevation_values[-1],
        label="Ende"
    )

    axis.set_title("3D-Darstellung der GPS-Route")

    axis.set_xlabel(
        "Westen ← Entfernung Ost [m] → Osten"
    )

    axis.set_ylabel(
        "Süden ← Entfernung Nord [m] → Norden"
    )

    axis.set_zlabel("Höhe [m]")

    axis.legend()

    plt.tight_layout()
    plt.savefig(
        OUTPUT_PATH,
        dpi=300
    )

    plt.show()


def main():
    if not CSV_PATH.exists():
        print(
            "CSV-Datei wurde nicht gefunden:"
        )
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

    print(
        f"Anzahl GPS-Punkte: "
        f"{len(latitude_values)}"
    )

    print(
        f"Minimale Höhe: "
        f"{min(elevation_values):.2f} m"
    )

    print(
        f"Maximale Höhe: "
        f"{max(elevation_values):.2f} m"
    )

    plot_3d_route(
        east_values,
        north_values,
        elevation_values
    )


if __name__ == "__main__":
    main()