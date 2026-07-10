import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize


class Plotter:

    def __init__(self):
        self.output_dir = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "processed"
            / "plots"
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)

    #--------------------------------------------------------------------------------------

    def plot_velocity(self, time, velocity):

        plt.figure(figsize=(10, 5))

        plt.plot(time, velocity)

        plt.title("Geschwindigkeit")

        plt.xlabel("Zeit [s]")

        plt.ylabel("Geschwindigkeit [m/s]")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(self.output_dir / "geschwindigkeit.png")

        plt.show()

    #----------------------------------------------------------------------------------

    def plot_power(self, time, power):

        plt.figure(figsize=(10, 5))

        plt.plot(time, power)

        plt.title("Leistung")

        plt.xlabel("Zeit [s]")

        plt.ylabel("Leistung [W]")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(self.output_dir / "leistung.png")

        plt.show()

    #------------------------------------------------------------------------------------

    def plot_motor_current(self, time, current):

        plt.figure(figsize=(10, 5))

        plt.plot(time, current)

        plt.title("Motorstrom")

        plt.xlabel("Zeit [s]")

        plt.ylabel("Motorstrom [A]")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(self.output_dir / "motorstrom.png")

        plt.show()

    #-------------------------------------------------------------------

    def plot_soc(self, time, soc_lipo, soc_nmc):

        plt.figure(figsize=(10, 5))

        plt.plot(time, soc_lipo * 100, label="LiPo")

        plt.plot(time, soc_nmc * 100, label="NMC")

        plt.title("Ladezustand")

        plt.xlabel("Zeit [s]")

        plt.ylabel("SOC [%]")

        plt.legend()

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(self.output_dir / "soc_vergleich.png")

        plt.show()

    #--------------------------------------------------------------------

    def plot_height_profile(self, distance, height):

        plt.figure(figsize=(12, 5))

        plt.plot(distance, height)

        plt.title("Höhenprofil")

        plt.xlabel("Strecke [m]")

        plt.ylabel("Höhe [m]")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(self.output_dir / "hoehenprofil.png")

        plt.show()

    #------------------------------------------------------------------------

    def plot_colored_gradient(self, distance, height, gradient):

    # Pandas-Serien in NumPy-Arrays umwandeln
        distance = np.asarray(distance, dtype=float) / 1000
        height = np.asarray(height, dtype=float)
        gradient = np.asarray(gradient, dtype=float)

    # Ungültige Werte ersetzen
        gradient = np.nan_to_num(
            gradient,
            nan=0.0,
            posinf=15.0,
            neginf=-15.0
        )

    # Punkte des Höhenprofils erzeugen
        points = np.column_stack((distance, height))

    # Einzelne Linienabschnitte erzeugen
        segments = np.stack(
            (points[:-1], points[1:]),
            axis=1
        )

        norm = Normalize(vmin=-15, vmax=15)

        colored_line = LineCollection(
            segments,
            cmap="coolwarm",
            norm=norm,
            linewidth=3
        )

        colored_line.set_array(gradient[:-1])

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.add_collection(colored_line)

        ax.set_xlim(distance.min(), distance.max())

        hoehen_abstand = max((height.max() - height.min()) * 0.05, 5)

        ax.set_ylim(
            height.min() - hoehen_abstand,
            height.max() + hoehen_abstand
        )

        ax.set_title("Höhenprofil mit Steigung")
        ax.set_xlabel("Distanz / km")
        ax.set_ylabel("Höhe / m")
        ax.grid(True, alpha=0.3)

        colorbar = fig.colorbar(
            colored_line,
            ax=ax,
            pad=0.02
        )

        colorbar.set_label("Steigung / %")

        plt.tight_layout()

        plt.savefig(
            self.output_dir / "hoehenprofil_steigung.png",
            dpi=300,
            bbox_inches="tight"
        )

        plt.show()