import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d.art3d import Line3DCollection

class Plotter:

    def __init__(self):
        self.output_dir = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "processed"
            / "plots"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

    def plot_colored_gradient(self, distance, height, gradient):
        distance = np.asarray(distance, dtype=float) / 1000
        height = np.asarray(height, dtype=float)
        gradient = np.asarray(gradient, dtype=float)

        gradient = np.nan_to_num(
            gradient,
            nan=0.0,
            posinf=15.0,
            neginf=-15.0
        )

        points = np.column_stack((distance, height))
        segments = np.stack((points[:-1], points[1:]), axis=1)
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
        ax.set_ylim(height.min() - hoehen_abstand, height.max() + hoehen_abstand)

        ax.set_title("Höhenprofil mit Steigung")
        ax.set_xlabel("Distanz / km")
        ax.set_ylabel("Höhe / m")
        ax.grid(True, alpha=0.3)

        colorbar = fig.colorbar(colored_line, ax=ax, pad=0.02)
        colorbar.set_label("Steigung / %")
        plt.tight_layout()
        plt.savefig(self.output_dir / "hoehenprofil_steigung.png", dpi=300, bbox_inches="tight")
        plt.show()

    # --- NEU: METHODE 2 (Windeinfluss als zeitbasierter Linienplot) ---
    def plot_wind_impact_timeline(self, time, heading, real_wind_speed, real_wind_dir):
        """Zeigt den Gegenwind- vs. Rückenwind-Effekt über die Zeitachse."""
        plt.figure(figsize=(10, 4.5))
        
        # Array-Umwandlung stellt sicher, dass mathematisch alles zusammenpasst
        heading_array = np.asarray(heading, dtype=float)
        
        # Effektiven Wind bestimmen (in km/h)
        angle_diff = np.radians(heading_array - real_wind_dir)
        effective_wind_kmh = (real_wind_speed * np.cos(angle_diff)) * 3.6
        
        # Zeit-Array auf die Länge der Winddaten kürzen (falls i-Slices abweichen)
        time_array = np.asarray(time, dtype=float)[:len(effective_wind_kmh)]
        effective_wind_kmh = effective_wind_kmh[:len(time_array)]
        
        plt.plot(time_array, effective_wind_kmh, color="#7f8c8d", linewidth=1.2)
        
        # Farbliche Füllung für Gegenwind (Rot) und Rückenwind (Grün)
        plt.fill_between(time_array, effective_wind_kmh, 0, 
                         where=(effective_wind_kmh > 0), color='#e74c3c', alpha=0.3, label="Gegenwind (Bremskraft)")
        plt.fill_between(time_array, effective_wind_kmh, 0, 
                         where=(effective_wind_kmh < 0), color='#2ecc71', alpha=0.3, label="Rückenwind (Schubkraft)")
        
        plt.xlabel("Zeit / s")
        plt.ylabel("Effektiver Wind / km/h")
        plt.title("Analyse des realen Windeinflusses im Fahrtverlauf")
        plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend()
        plt.tight_layout()
        plt.savefig(self.output_dir / "wind_verlauf_zeit.png", dpi=300)
        plt.show()

    # --- METHODE 3 (Die farbkodierte 3D-Route deines Kollegen) ---
    # --- METHODE 3 (Die farbkodierte 3D-Route deines Kollegen) ---
    def plot_3d_route_with_wind(self, east, north, height, heading, real_wind_speed, real_wind_dir):
        """Zeichnet die 3D-Route deines Kollegen, gefärbt nach der Windauswirkung."""
        fig = plt.figure(figsize=(11, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        x = np.asarray(east, dtype=float)
        y = np.asarray(north, dtype=float)
        z = np.asarray(height, dtype=float)
        heading_array = np.asarray(heading, dtype=float)  # <-- HIER: Saubere Definition für die Berechnung!
        
        # Berechnung der Windbelastung für jedes Segment
        angle_diff = np.radians(heading_array - real_wind_dir)
        wind_impact = (real_wind_speed * np.cos(angle_diff)) * 3.6
        
        points = np.array([x, y, z]).T.reshape(-1, 1, 3)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        # Farbkarte sauber laden (Grün = Rückenwind, Rot = Gegenwind)
        cmap = plt.get_cmap('RdYlGn_r')
        
        lc = Line3DCollection(segments, cmap=cmap, linewidths=3.5)
        lc.set_array(wind_impact[:-1])
        line = ax.add_collection3d(lc)
        
        # Start und Endpunkt als Markierung
        ax.scatter(x[0], y[0], z[0], color="blue", s=50, label="Start", zorder=5)
        ax.scatter(x[-1], y[-1], z[-1], color="orange", s=50, label="Ende", zorder=5)
        
        ax.set_xlim(x.min(), x.max())
        ax.set_ylim(y.min(), y.max())
        ax.set_zlim(z.min(), z.max())
        
        ax.set_title("3D-Streckenprofil mit farbkodiertem Windeinfluss", fontweight='bold', pad=20)
        ax.set_xlabel("Westen ← Entfernung Ost [m] → Osten")
        ax.set_ylabel("Süden ← Entfernung Nord [m] → Norden")
        ax.set_zlabel("Höhe [m]")
        ax.legend()
        
        cbar = fig.colorbar(line, ax=ax, pad=0.1, shrink=0.55)
        cbar.set_label("Effektive Windkomponente / km/h (Rot = Gegenwind)")
        
        plt.tight_layout()
        plt.savefig(self.output_dir / "route_3d_wind_farbcodiert.png", dpi=300)
        plt.show()