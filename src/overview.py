from pathlib import Path
import csv
from statistics import mean


PROJECT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_DIR / "data" / "raw" / "final_project_input_data.csv"
RESULTS_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_PATH = PROJECT_DIR / "RESULTS.md"


def load_temperatures():
    temperatures = []

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        delimiter = ";" if ";" in file.readline() else ","
        file.seek(0)

        reader = csv.DictReader(
            file,
            delimiter=delimiter
        )

        for row in reader:
            try:
                temperature = float(
                    row["temperature"].replace(",", ".")
                )
                temperatures.append(temperature)

            except (KeyError, ValueError, AttributeError):
                continue

    return temperatures


def create_results():
    temperatures = load_temperatures()

    # Sucht alle PNG-Dateien in data/processed
    # und in allen Unterordnern, zum Beispiel plots.
    plots = sorted(
        RESULTS_DIR.rglob("*.png")
    )

    content = "# Simulationsergebnisse\n\n"

    if temperatures:
        content += "## Wetterdaten\n\n"
        content += "| Messgröße | Wert |\n"
        content += "|---|---:|\n"
        content += (
            f"| Minimale Temperatur | "
            f"{min(temperatures):.2f} °C |\n"
        )
        content += (
            f"| Maximale Temperatur | "
            f"{max(temperatures):.2f} °C |\n"
        )
        content += (
            f"| Durchschnittstemperatur | "
            f"{mean(temperatures):.2f} °C |\n"
        )
        content += (
            f"| Anzahl der Messwerte | "
            f"{len(temperatures)} |\n\n"
        )

    content += "## Diagramme\n\n"

    if not plots:
        content += "Es wurden keine Diagramme gefunden.\n"

    for plot in plots:
        title = (
            plot.stem
            .replace("_", " ")
            .replace("-", " ")
            .title()
        )

        path = plot.relative_to(
            PROJECT_DIR
        ).as_posix()

        content += f"### {title}\n\n"
        content += f"![{title}]({path})\n\n"

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8"
    )

    print(f"Übersicht erstellt: {OUTPUT_PATH}")
    print(f"Gefundene Diagramme: {len(plots)}")

    for plot in plots:
        print(f"  - {plot.name}")


if __name__ == "__main__":
    create_results()