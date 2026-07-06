import pandas as pd
import numpy as np

class GPSDataLoader:
    def __init__(self, file_path: str):
        """Initialisiert den Loader und lädt die CSV-Daten."""
        self.file_path = file_path
        self.df = None

    def load_and_clean_data(self) -> pd.DataFrame:
        """Lädt die GPS-Daten fehlertolerant und bereitet sie vor."""
        # 1. CSV einlesen: Wir versuchen Komma, fallen bei Bedarf auf Semikolon zurück
        try:
            self.df = pd.read_csv(self.file_path, sep=',')
            # Falls pandas alles in eine einzige Spalte packt, war es wohl ein Semikolon
            if len(self.df.columns) <= 1:
                self.df = pd.read_csv(self.file_path, sep=';')
        except Exception:
            self.df = pd.read_csv(self.file_path, sep=';')
        
        # 2. Spaltennamen von Leerzeichen befreien und in Kleinbuchstaben umwandeln
        self.df.columns = self.df.columns.str.strip().str.lower()
        
        # 3. Flexible Erkennung alternativer Spaltennamen (z.B. 'time' statt 'timestamp')
        if 'time' in self.df.columns and 'timestamp' not in self.df.columns:
            self.df = self.df.rename(columns={'time': 'timestamp'})
        if 'altitude' in self.df.columns and 'ele' not in self.df.columns:
            self.df = self.df.rename(columns={'altitude': 'ele'})
            
        # Sicherheits-Check für dich im Terminal
        print("Erkannte CSV-Spalten nach Bereinigung:", self.df.columns.tolist())
        
        # 4. Zeitstempel in echtes DateTime-Objekt konvertieren
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        # 5. Zeitdifferenz delta_t in Sekunden berechnen
        self.df['delta_t'] = self.df['timestamp'].diff().dt.total_seconds()
        self.df['delta_t'] = self.df['delta_t'].fillna(0.0)
        
        # 6. Höhenprofil glätten
        if 'ele' in self.df.columns:
            self.df['ele_smoothed'] = self.df['ele'].rolling(window=5, min_periods=1, center=True).mean()
        else:
            self.df['ele_smoothed'] = 0.0
            
        return self.df