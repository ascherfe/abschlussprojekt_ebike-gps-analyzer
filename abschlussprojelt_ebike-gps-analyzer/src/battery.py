import numpy as np
import logging

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
        self.cells_series = cells_series
        self.cells_parallel = cells_parallel
        self.capacity_ah = capacity_ah
        self.soc = initial_soc

        self.soc_points = np.array([])
        self.ocv_points = np.array([])

        self.internal_resistance_cell = 0.0

        self.check_soc()

    def check_soc(self):
        if self.soc < 0:
            logging.warning("SOC unter 0 %. Wert wird auf 0 gesetzt.")
            self.soc = 0

        if self.soc > 1:
            logging.warning("SOC über 100 %. Wert wird auf 100 % gesetzt.")
            self.soc = 1

    def get_ocv(self):
        self.check_soc()
        return np.interp(self.soc, self.soc_points, self.ocv_points)

    def get_total_resistance(self):
        return self.internal_resistance_cell * self.cells_series / self.cells_parallel

    def get_terminal_voltage(self, current):
        return self.get_ocv() - current * self.get_total_resistance()

    def discharge(self, current, dt_seconds):
        if current < 0:
            current = 0

        used_ah = current * dt_seconds / 3600
        total_capacity = self.capacity_ah * self.cells_parallel

        self.soc -= used_ah / total_capacity
        self.check_soc()

        logging.info(f"SOC: {self.soc * 100:.2f} %")

        return self.soc


class LiPoBattery(Battery):
    def __init__(self, cells_series=10, cells_parallel=1, capacity_ah=10, initial_soc=1.0):
        super().__init__(cells_series, cells_parallel, capacity_ah, initial_soc)

        self.internal_resistance_cell = 0.008

        self.soc_points = np.array([
            0.00, 0.04, 0.09, 0.13, 0.17, 0.21, 0.26,
            0.30, 0.40, 0.52, 0.64, 0.76, 0.88, 1.00
        ])

        self.ocv_points = np.array([
            32.00, 35.87, 36.85, 37.56, 37.87, 38.28, 38.81,
            39.05, 39.55, 40.27, 40.70, 41.16, 41.65, 42.00
        ])


class NMCBattery(Battery):
    def __init__(self, cells_series=10, cells_parallel=1, capacity_ah=10, initial_soc=1.0):
        super().__init__(cells_series, cells_parallel, capacity_ah, initial_soc)

        self.internal_resistance_cell = 0.007

        self.soc_points = np.array([
            0.00, 0.04, 0.09, 0.13, 0.17, 0.21, 0.26,
            0.30, 0.40, 0.52, 0.64, 0.76, 0.88, 1.00
        ])

        self.ocv_points = np.array([
            32.00, 32.61, 33.17, 33.85, 34.24, 34.66, 35.39,
            35.65, 36.65, 37.64, 38.91, 40.14, 41.08, 42.00
        ])