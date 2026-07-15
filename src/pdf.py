from pathlib import Path
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


class PDFReport:
    """Erstellt einen sauberen, mehrseitigen Ergebnisbericht der E-Bike-Simulation als PDF."""

    def __init__(self, output_path: Path):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def create_report(self, results: dict, plot_paths: list[Path]) -> None:
        """Erstellt das PDF-Dokument mit der strukturierten Übersicht und den Diagrammen."""
        with PdfPages(self.output_path) as pdf:
            # 1. Seite: Strukturierte Textübersicht mit allen Kennwerten
            self._create_overview_page(pdf, results)

            # Folgeseiten: Jedes Diagramm mit einer kurzen Erklärung auf eine eigene Seite packen
            for plot_path in plot_paths:
                self._add_plot_page(pdf, Path(plot_path))

        print(f"PDF-Bericht wurde erfolgreich erstellt: {self.output_path}")

    @staticmethod
    def _create_overview_page(pdf: PdfPages, results: dict) -> None:
        """Erstellt die erste Seite des Berichts mit sauber strukturierten Tabellen/Sektionen."""
        # A4-Format in Zoll definieren (Hochformat)
        figure = plt.figure(figsize=(8.27, 11.69))
        
        # Haupttitel
        figure.suptitle(
            "E-Bike GPS Analyzer & Simulationsbericht",
            fontsize=18,
            fontweight="bold",
            y=0.95,
        )

        # Untertitel / Meta-Infos
        figure.text(
            0.08,
            0.91,
            "Systematische Auswertung der GPS-Fahrdaten und der Akku-Simulation",
            fontsize=11,
            style="italic"
        )

        # Wir teilen die Ergebnisse in logische Sektionen auf
        sections = [
            {
                "title": "1. Allgemeine Strecken- & Zeitdaten",
                "keys": ["Anzahl GPS-Punkte", "Gesamtstrecke", "Gesamte Fahrtzeit", "Durchschnittsgeschwindigkeit", "Maximale Geschwindigkeit"]
            },
            {
                "title": "2. Höhenprofil & Geländecharakteristik",
                "keys": ["Minimale Höhe", "Maximale Höhe", "Höhenunterschied", "Positive Höhenmeter", "Negative Höhenmeter"]
            },
            {
                "title": "3. Motorleistung & elektrische Messwerte",
                "keys": ["Durchschnittliche Motorleistung", "Maximale Motorleistung", "Durchschnittlicher Motorstrom", "Maximaler Motorstrom"]
            },
            {
                "title": "4. Akkusimulation (End-Ladezustände)",
                "keys": ["LiPo-Ladezustand am Ende", "NMC-Ladezustand am Ende"]
            },
            {
                "title": "5. Reale Wetterbedingungen beim Start",
                "keys": ["Reale Windgeschwindigkeit", "Reale Windrichtung"]
            }
        ]

        y_position = 0.84

        for section in sections:
            # Sektionstitel zeichnen
            figure.text(
                0.08,
                y_position,
                section["title"],
                fontsize=12,
                fontweight="bold",
                color="#2c3e50"
            )
            y_position -= 0.025

            # Werte für diese Sektion heraussuchen und untereinander auflisten
            for key in section["keys"]:
                if key in results:
                    value = results[key]
                    
                    # Parametername links bündig
                    figure.text(
                        0.10,
                        y_position,
                        f"{key}:",
                        fontsize=10,
                        color="#34495e"
                    )
                    
                    # Berechneter Wert rechts bündig (tabellarisch verschoben)
                    figure.text(
                        0.60,
                        y_position,
                        str(value),
                        fontsize=10,
                        fontweight="bold",
                        color="#2c3e50"
                    )
                    y_position -= 0.023

            # Kleiner Abstand zur nächsten Sektion
            y_position -= 0.025

        # Fußzeile auf der ersten Seite
        figure.text(
            0.08,
            0.04,
            "Erstellt mit dem E-Bike-GPS-Analyzer (MCI Programmieren I Abschlussprojekt).",
            fontsize=8,
            color="#7f8c8d"
        )

        pdf.savefig(figure, bbox_inches="tight")
        plt.close(figure)

    @staticmethod
    def _add_plot_page(pdf: PdfPages, plot_path: Path) -> None:
        """Packt ein Diagramm auf eine eigene Querformat-Seite und fügt eine Erklärung hinzu."""
        if not plot_path.exists():
            print(f"Diagramm übersprungen (Datei fehlt): {plot_path}")
            return

        # Bild einlesen
        image = mpimg.imread(plot_path)

        # A4-Format im Querformat anlegen
        figure, axis = plt.subplots(figsize=(11.69, 8.27))

        # Bild auf der Achse darstellen und die Achsenstriche ausblenden
        axis.imshow(image)
        axis.axis("off")

        # Dynamischer Titel basierend auf dem Dateinamen
        title_text = plot_path.stem.replace("_", " ").title()
        figure.suptitle(
            title_text,
            fontsize=16,
            fontweight="bold",
            y=0.94,
        )

        # Kurze, studentische Beschreibungen zu jedem Diagramm hinzufügen,
        # damit das PDF wissenschaftlich aussieht und echten Informationsgehalt hat.
        description = "Visualisierung der berechneten Simulationsergebnisse."
        
        filename = plot_path.name.lower()
        if "geschwindigkeit" in filename:
            description = (
                "Das Diagramm zeigt das Geschwindigkeitsprofil über die Zeitachse. "
                "Gut zu erkennen sind Beschleunigungsphasen sowie fahrbahnspezifische Bremsungen."
            )
        elif "motorleistung" in filename:
            description = (
                "Verlauf der vom Motor abgerufenen mechanischen Leistung. "
                "Deutlich sichtbar ist die automatische Deckelung bei der gesetzlichen Grenze von 500 Watt."
            )
        elif "akkuladestand" in filename or "soc_vergleich" in filename:
            description = (
                "Direkter Vergleich des State of Charge (SOC) von LiPo (12 Ah) und NMC (16 Ah) über die Fahrt. "
                "Der NMC-Akku weist aufgrund der höheren Nennkapazität am Ende der Route mehr Restenergie auf."
            )
        elif "motorstrom" in filename:
            description = (
                "Verlauf des entnommenen Motorstroms in Ampere. "
                "Der Strom skaliert proportional zum benötigten Drehmoment an Steigungen und beim Anfahren."
            )
        elif "hoehenprofil_steigung" in filename:
            description = (
                "Gefahrene Route über die Distanz. Die farbliche Codierung visualisiert "
                "die prozentuale Steigung (Rot = steile Anstiege, Blau = Gefälle)."
            )
        elif "hoehenprofil" in filename:
            description = (
                "Das klassische Höhenprofil über die gesamte Distanz. "
                "Dient zur Lokalisierung der anspruchsvollsten Bergpassagen der Tour."
            )
        elif "wind_verlauf" in filename:
            description = (
                "Zeigt den Windeinfluss bezogen auf die Fahrtrichtung. "
                "Rote Flächen bedeuten Gegenwind (Bremskraft), grüne Flächen zeigen unterstützenden Rückenwind."
            )
        elif "route_3d" in filename:
            description = (
                "Dreidimensionale Rekonstruktion der Fahrtroute im lokalen Koordinatennetz (Osten/Norden/Höhe). "
                "Die Färbung der Route zeigt an, wie stark der Wind lokal auf den Fahrer gewirkt hat."
            )
        elif "parameter" in filename:
            description = (
                "Ergebnisse der Parameterstudie. Dargestellt ist der Ladezustand beider Akkutypen "
                "für drei verschiedene Fahrer-Gewichtsklassen und Reifenwiderstände."
            )

        # Erklärungstext unten auf der Seite platzieren
        figure.text(
            0.10,
            0.06,
            f"Anmerkung: {description}",
            fontsize=10,
            style="italic",
            color="#34495e"
        )

        pdf.savefig(figure, bbox_inches="tight")
        plt.close(figure)