from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


class PDFReport:
    """Erstellt eine PDF aus Ergebnissen und gespeicherten Diagrammen."""

    def __init__(self, output_path: Path):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def create_report(
        self,
        results: dict,
        plot_paths: list[Path],
    ) -> None:
        """
        Erstellt eine mehrseitige PDF.

        Parameters
        ----------
        results:
            Dictionary mit Namen und berechneten Werten.

        plot_paths:
            Liste mit den Pfaden zu den Diagrammen.
        """

        with PdfPages(self.output_path) as pdf:
            self._create_overview_page(pdf, results)

            for plot_path in plot_paths:
                self._add_plot_page(pdf, Path(plot_path))

        print(f"PDF-Bericht wurde erstellt: {self.output_path}")

    @staticmethod
    def _create_overview_page(pdf: PdfPages, results: dict) -> None:
        """Erstellt die erste Seite mit allen berechneten Werten."""

        figure = plt.figure(figsize=(8.27, 11.69))
        figure.suptitle(
            "E-Bike GPS Analyzer – Ergebnisübersicht",
            fontsize=18,
            fontweight="bold",
            y=0.96,
        )

        figure.text(
            0.08,
            0.91,
            "Zusammenfassung der berechneten Fahr- und Simulationsdaten",
            fontsize=11,
        )

        y_position = 0.85

        for name, value in results.items():
            figure.text(
                0.10,
                y_position,
                str(name),
                fontsize=11,
                fontweight="bold",
            )

            figure.text(
                0.55,
                y_position,
                str(value),
                fontsize=11,
            )

            y_position -= 0.045

            # Neue Seite beginnen, falls zu viele Werte vorhanden sind
            if y_position < 0.08:
                pdf.savefig(figure, bbox_inches="tight")
                plt.close(figure)

                figure = plt.figure(figsize=(8.27, 11.69))
                figure.suptitle(
                    "Weitere Ergebnisse",
                    fontsize=18,
                    fontweight="bold",
                    y=0.96,
                )

                y_position = 0.88

        pdf.savefig(figure, bbox_inches="tight")
        plt.close(figure)

    @staticmethod
    def _add_plot_page(pdf: PdfPages, plot_path: Path) -> None:
        """Fügt ein gespeichertes Diagramm als eigene PDF-Seite ein."""

        if not plot_path.exists():
            print(f"Diagramm nicht gefunden und übersprungen: {plot_path}")
            return

        image = mpimg.imread(plot_path)

        figure, axis = plt.subplots(figsize=(11.69, 8.27))

        axis.imshow(image)
        axis.axis("off")

        figure.suptitle(
            plot_path.stem.replace("_", " ").title(),
            fontsize=16,
            fontweight="bold",
        )

        pdf.savefig(figure, bbox_inches="tight")
        plt.close(figure)