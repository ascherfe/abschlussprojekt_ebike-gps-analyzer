import numpy as np
import logging

# Log-Level auf INFO setzen, damit die DEBUG-Ausgaben beim Entladen das Terminal nicht fluten
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


class Battery:
    def __init__(
        self,
        cells_series=10,
        cells_parallel=1,
        capacity_ah=10,
        initial_soc=1.0
    ):
        # Basis-Parameter für die Akkus setzen
        self.cells_series = cells_series
        self.cells_parallel = cells_parallel
        self.capacity_ah = capacity_ah
        self.soc = initial_soc

        # Diese Arrays werden in den Unterklassen mit den Kennlinien gefüllt
        self.soc_points = np.array([])
        self.ocv_points = np.array([])

        # Innenwiderstand einer einzelnen Zelle (wird unten überschrieben)
        self.internal_resistance_cell = 0.0

        # Start-SOC einmal überprüfen
        self.check_soc()

    def check_soc(self):
        """
        Stellt sicher, dass der Ladezustand immer zwischen 0.0 und 1.0 (0% und 100%) bleibt.
        """
        if self.soc < 0.0:
            logging.warning("Ladezustand war unter 0%. Setze SOC auf 0.0.")
            self.soc = 0.0

        if self.soc > 1.0:
            logging.warning("Ladezustand war ueber 100%. Setze SOC auf 1.0.")
            self.soc = 1.0

    def get_ocv(self):
        """
        Berechnet die Leerlaufspannung (Open Circuit Voltage) passend zum aktuellen SOC.
        Nutzt lineare Interpolation zwischen den Stützpunkten der Kennlinie.
        """
        self.check_soc()
        return np.interp(self.soc, self.soc_points, self.ocv_points)

    def get_total_resistance(self):
        """
        Berechnet den Gesamt-Innenwiderstand des Akkupacks basierend auf der Verschaltung.
        Formel: R_gesamt = R_zelle * Seriell-Zellen / Parallel-Zellen
        """
        return self.internal_resistance_cell * self.cells_series / self.cells_parallel

    def get_terminal_voltage(self, current):
        """
        Berechnet die Klemmenspannung unter Last (Spannungsabfall am Innenwiderstand).
        Formel: U_klemme = U_ocv - I * R_gesamt
        """
        return self.get_ocv() - current * self.get_total_resistance()

    def discharge(self, current, dt_seconds):
        """
        Simuliert die Entladung über ein kleines Zeitintervall (dt).
        Berechnet die verbrauchten Amperestunden und aktualisiert den Ladezustand.
        """
        # Wenn kein Strom fließt (oder negativ beim Bremsen), entladen wir nicht
        if current < 0:
            current = 0

        # Verbrauchte Amperestunden in diesem Zeitschritt
        used_ah = current * dt_seconds / 3600
        
        # Gesamtkapazität des Packs (Kapazität einer Zelle * Anzahl Parallelschaltungen)
        total_capacity = self.capacity_ah * self.cells_parallel

        # SOC anpassen und kontrollieren
        self.soc -= used_ah / total_capacity
        self.check_soc()

        # Als Debug loggen, damit das normale Terminal nicht vollgespammt wird
        logging.debug(f"SOC: {self.soc * 100:.2f} %")

        return self.soc


class LiPoBattery(Battery):
    def __init__(self, cells_series=10, cells_parallel=1, capacity_ah=10, initial_soc=1.0):
        super().__init__(cells_series, cells_parallel, capacity_ah, initial_soc)

        # 8 mOhm Innenwiderstand pro Zelle laut Folie
        self.internal_resistance_cell = 0.008

        # SOC-Stützpunkte für die Kennlinie
        self.soc_points = np.array([
            0.00, 0.04, 0.09, 0.13, 0.17, 0.21, 0.26,
            0.30, 0.40, 0.52, 0.64, 0.76, 0.88, 1.00
        ])

        # Zugehörige Spannungen (OCV) für das Akkupack (10S-Verschaltung)
        self.ocv_points = np.array([
            32.00, 35.87, 36.85, 37.56, 37.87, 38.28, 38.81,
            39.05, 39.55, 40.27, 40.70, 41.16, 41.65, 42.00
        ])


class NMCBattery(Battery):
    def __init__(self, cells_series=10, cells_parallel=1, capacity_ah=10, initial_soc=1.0):
        super().__init__(cells_series, cells_parallel, capacity_ah, initial_soc)

        # 7 mOhm Innenwiderstand pro Zelle laut Folie
        self.internal_resistance_cell = 0.007

        # SOC-Stützpunkte für die Kennlinie
        self.soc_points = np.array([
            0.00, 0.04, 0.09, 0.13, 0.17, 0.21, 0.26,
            0.30, 0.40, 0.52, 0.64, 0.76, 0.88, 1.00
        ])

        # Zugehörige Spannungen (OCV) für das Akkupack (10S-Verschaltung)
        self.ocv_points = np.array([
            32.00, 32.61, 33.17, 33.85, 34.24, 34.66, 35.39,
            35.65, 36.65, 37.64, 38.91, 40.14, 41.08, 42.00
        ])