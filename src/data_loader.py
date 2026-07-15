import pandas as pd
import numpy as np

class GPSDataLoader:
    def __init__(self, file_path: str):
        # Pfad zur CSV-Datei abspeichern
        self.file_path = file_path
        self.df = None

    def load_and_clean_data(self) -> pd.DataFrame:
        """
        Laedt die GPS-Daten ein, bereinigt die Spaltennamen,
        berechnet die Zeitabstaende und glaettet das Hoehenprofil.
        """
        # 1. CSV einlesen (versucht Komma, faellt sonst auf Semikolon zurueck)
        try:
            self.df = pd.read_csv(self.file_path, sep=',')
            # Falls alles in einer einzigen Spalte landet, war das Trennzeichen falsch
            if len(self.df.columns) <= 1:
                self.df = pd.read_csv(self.file_path, sep=';')
        except Exception:
            self.df = pd.read_csv(self.file_path, sep=';')
        
        # 2. Spaltennamen von Leerzeichen befreien und in Kleinbuchstaben umwandeln
        self.df.columns = self.df.columns.str.strip().str.lower()
        
        # 3. Alternative Spaltennamen korrigieren, falls noetig
        if 'time' in self.df.columns and 'timestamp' not in self.df.columns:
            self.df = self.df.rename(columns={'time': 'timestamp'})
        if 'altitude' in self.df.columns and 'ele' not in self.df.columns:
            self.df = self.df.rename(columns={'altitude': 'ele'})
            
        print("Gefundene Spalten nach der Bereinigung:", self.df.columns.tolist())
        
        # 4. Datetime-Konvertierung fuer die Zeitberechnungen
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        # 5. Zeitdifferenz (delta_t) in Sekunden berechnen
        self.df['delta_t'] = self.df['timestamp'].diff().dt.total_seconds()
        self.df['delta_t'] = self.df['delta_t'].fillna(0.0)
        
        # 6. Glaettung der Hoehendaten mit einem gleitenden Mittelwert (Fenstergroesse = 5)
        if 'ele' in self.df.columns:
            self.df['ele_smoothed'] = self.df['ele'].rolling(window=5, min_periods=1, center=True).mean()
        else:
            self.df['ele_smoothed'] = 0.0
            
        return self.df