import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


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

        plt.figure(figsize=(12, 5))

        gradient = np.asarray(gradient)

        for i in range(len(distance) - 1):

            if gradient[i] > 5:

                color = "red"

            elif gradient[i] > 2:

                color = "orange"

            elif gradient[i] > -2:

                color = "green"

            elif gradient[i] > -5:

                color = "cyan"

            else:

                color = "blue"

            plt.plot(
                distance[i:i + 2],
                height[i:i + 2],
                color=color,
                linewidth=2
            )

        plt.title("Höhenprofil mit Steigung")

        plt.xlabel("Strecke [m]")

        plt.ylabel("Höhe [m]")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(self.output_dir / "hoehenprofil_steigung.png")

        plt.show()