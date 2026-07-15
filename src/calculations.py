import numpy as np
import pandas as pd
import openmeteo_requests
import requests_cache
from retry import retry

class PhysicsCalculator:
    def __init__(self, total_mass: float = 80.0, cw: float = 0.9, area: float = 0.625, rho: float = 1.225, cr: float = 0.004):
        """
        Hier setzen wir die physikalischen Standardwerte.
        Masse: 80 kg (70 kg Fahrer + 10 kg Bike laut Folie).
        cw * A ergibt genau 0.5625 m² wie vorgegeben.
        """
        self.m = total_mass
        self.cw = cw
        self.A = area
        self.rho = rho
        self.cr = cr
        self.g = 9.81

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Berechnet den Abstand zwischen zwei GPS-Punkten auf der Erdkugel in Metern.
        """
        R = 6371000.0  # Erdradius in m
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)
        
        a = np.sin(delta_phi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0)**2
        c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
        return R * c

    @staticmethod
    def calculate_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Berechnet die Fahrtrichtung in Grad (0° = Norden, 90° = Osten).
        Wichtig, um spaeter den Winkel zum Wind zu bestimmen.
        """
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        delta_lambda = np.radians(lon2 - lon1)
        y = np.sin(delta_lambda) * np.cos(phi2)
        x = np.cos(phi1) * np.sin(phi2) - np.sin(phi1) * np.cos(phi2) * np.cos(delta_lambda)
        heading = np.degrees(np.arctan2(y, x))
        return (heading + 360.0) % 360.0

    def fetch_real_weather_data(self, lat: float, lon: float, timestamp: pd.Timestamp):
        """
        Holt historische Winddaten ueber die Open-Meteo API passend zum Fahrtzeitpunkt.
        """
        print(f"Hole Wetterdaten fuer ({lat:.4f}, {lon:.4f}) am {timestamp.strftime('%Y-%m-%d %H:%M')}...")
        
        # Cache einrichten, damit wir die API nicht bei jedem Start spammen
        cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
        retry_session = retry(tries=5, delay=2)(cache_session)
        openmeteo = openmeteo_requests.Client(session=retry_session)

        date_str = timestamp.strftime('%Y-%m-%d')
        hour_of_ride = timestamp.hour

        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": ["wind_speed_10m", "wind_direction_10m"]
        }
        
        try:
            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]
            hourly = response.Hourly()
            
            # API liefert km/h, wir brauchen m/s fuer die Formeln
            wind_speeds_kmh = hourly.Variables(0).ValuesAsNumpy()
            wind_directions = hourly.Variables(1).ValuesAsNumpy()
            
            real_wind_speed_ms = (wind_speeds_kmh[hour_of_ride]) / 3.6
            real_wind_direction = float(wind_directions[hour_of_ride])
            
            print(f"-> Wind: {real_wind_speed_ms*3.6:.1f} km/h aus {real_wind_direction}°")
            return real_wind_speed_ms, real_wind_direction
            
        except Exception as e:
            print(f"API-Fehler ({e}). Setze Windstille als Fallback.")
            return 0.0, 0.0

    def calculate_metrics(self, df: pd.DataFrame, wind_speed: float = 0.0, wind_direction: float = 0.0) -> pd.DataFrame:
        """
        Rechnet die komplette fahrphysikalische Simulation fuer jeden Punkt durch.
        """
        distances, speeds, accelerations, slopes, f_vortrieb, headings = [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]
        
        for i in range(1, len(df)):
            lat1, lon1 = df.loc[i-1, 'lat'], df.loc[i-1, 'lon']
            lat2, lon2 = df.loc[i, 'lat'], df.loc[i, 'lon']
            dt = df.loc[i, 'delta_t']
            
            # 1. Distanz berechnen
            ds = self.haversine_distance(lat1, lon1, lat2, lon2)
            distances.append(ds)
            
            if dt > 0 and ds > 0:
                # 2. Geschwindigkeit & Beschleunigung
                v = ds / dt
                speeds.append(v)
                
                dv = v - speeds[i-1]
                a = dv / dt
                accelerations.append(a)
                
                # 3. Steigung bestimmen (Hoehendifferenz geteilt durch Strecke)
                dh = df.loc[i, 'ele_smoothed'] - df.loc[i-1, 'ele_smoothed']
                phi = np.arcsin(clamp(dh / ds, -1.0, 1.0))
                slopes.append(phi)
                
                # 4. Fahrtrichtung & effektiven Wind berechnen
                current_heading = self.calculate_heading(lat1, lon1, lat2, lon2)
                headings.append(current_heading)
                
                angle_diff = np.radians(current_heading - wind_direction)
                effective_wind = wind_speed * np.cos(angle_diff)
                
                # Relativgeschwindigkeit zum Wind (darf nicht negativ werden beim Quadrieren)
                v_rel = max(0.0, v + effective_wind)
                
                # 5. Kraefte-Berechnung laut den Vorlesungsfolien
                f_air = 0.5 * self.rho * self.cw * self.A * (v_rel**2)  # Luftwiderstand
                f_slope = self.m * self.g * np.sin(phi)                # Hangabtrieb
                f_acc = self.m * a                                     # Beschleunigungskraft
                f_roll = self.cr * self.m * self.g * np.cos(phi)       # Rollwiderstand
                
                f_total = f_air + f_slope + f_acc + f_roll
                f_vortrieb.append(max(0.0, f_total))
            else:
                # Fallback, falls das Fahrrad steht
                speeds.append(speeds[-1])
                accelerations.append(0.0)
                slopes.append(slopes[-1])
                f_vortrieb.append(0.0)
                headings.append(headings[-1])
                
        df['distance_delta'] = distances
        df['speed'] = speeds
        df['acceleration'] = accelerations
        df['slope_angle'] = slopes
        df['heading'] = headings
        df['force_vortrieb'] = f_vortrieb
        return df


def clamp(n, minn, maxn):
    """Hilfsfunktion, um Werte in einem Bereich zu halten (wichtig fuer arcsin)"""
    return max(min(n, maxn), minn)