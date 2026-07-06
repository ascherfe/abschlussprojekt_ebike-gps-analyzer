import numpy as np
import pandas as pd

class PhysicsCalculator:
    def __init__(self, total_mass: float = 100.0, cw: float = 0.9, area: float = 0.6, rho: float = 1.225):
        """
        Konstruktor für die physikalischen Konstanten.
        :param total_mass: Masse von Fahrer + E-Bike in kg (z.B. 100 kg)
        :param cw: Luftwiderstandsbeiwert (Strömungswiderstandskoeffizient)
        :param area: Stirnfläche des Fahrers in m^2
        :param rho: Luftdichte in kg/m^3 (Standard: 1.225 bei Meeresspiegel)
        """
        self.m = total_mass
        self.cw = cw
        self.A = area
        self.rho = rho
        self.g = 9.81 # Erdbeschleunigung in m/s^2

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Berechnet die Distanz zwischen zwei GPS-Punkten in Metern."""
        R = 6371000.0 # Erdradius in Metern
        
        # Umrechnung von Grad in Bogenmaß (Rad)
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)
        
        # Haversine-Formel
        a = np.sin(delta_phi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0)**2
        c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
        
        return R * c

    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Berechnet Strecke, v, a, Steigung und die benötigte Gesamtkraft für jeden Punkt."""
        
        # Arrays für die Ergebnisse vorbereiten
        distances = [0.0]
        speeds = [0.0]
        accelerations = [0.0]
        slopes = [0.0]
        f_vortrieb = [0.0]
        
        for i in range(1, len(df)):
            lat1, lon1 = df.loc[i-1, 'lat'], df.loc[i-1, 'lon']
            lat2, lon2 = df.loc[i, 'lat'], df.loc[i, 'lon']
            dt = df.loc[i, 'delta_t']
            
            # 1. Distanz berechnen
            ds = self.haversine_distance(lat1, lon1, lat2, lon2)
            distances.append(ds)
            
            if dt > 0:
                # 2. Geschwindigkeit v = ds / dt
                v = ds / dt
                speeds.append(v)
                
                # 3. Beschleunigung a = dv / dt
                dv = v - speeds[i-1]
                a = dv / dt
                accelerations.append(a)
                
                # 4. Steigung (Winkel phi) bestimmen
                dh = df.loc[i, 'ele_smoothed'] - df.loc[i-1, 'ele_smoothed']
                # Steigungswinkel über Geometrie (sin(phi) = dh / ds)
                if ds > 0:
                    phi = np.arcsin(clamp(dh / ds, -1.0, 1.0))
                else:
                    phi = 0.0
                slopes.append(phi)
                
                # 5. KRAFT-BERECHNUNG (Freikörperdiagramm aus eurer Aufgabe)
                # F_Luft = 0.5 * rho * cw * A * v^2
                f_air = 0.5 * self.rho * self.cw * self.A * (v**2)
                # F_Hang = m * g * sin(phi)
                f_slope = self.m * self.g * np.sin(phi)
                # F_Beschleunigung = m * a
                f_acc = self.m * a
                
                # Gesamte Vortriebskraft, die das E-Bike aufbringen muss
                f_total = f_air + f_slope + f_acc
                f_vortrieb.append(max(0.0, f_total)) # Keine negative Kraft beim Bremsen simulieren
                
            else:
                speeds.append(speeds[-1])
                accelerations.append(0.0)
                slopes.append(slopes[-1])
                f_vortrieb.append(0.0)
                
        # Spalten an das DataFrame anhängen
        df['distance_delta'] = distances
        df['speed'] = speeds
        df['acceleration'] = accelerations
        df['slope_angle'] = slopes
        df['force_vortrieb'] = f_vortrieb
        
        return df

def clamp(n, minn, maxn):
    """Hilfsfunktion, um Werte mathematisch im Intervall [-1, 1] zu halten."""
    return max(min(n, maxn), minn)