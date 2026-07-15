class Motor:
    def __init__(self, wheel_diameter_inch=27, motor_constant=1.5):
        # 27 Zoll Rad und 1.5 Nm/A Motorkonstante
        self.wheel_diameter_inch = wheel_diameter_inch
        self.motor_constant = motor_constant
        
        # Umrechnung von Zoll in Meter für den Radradius
        self.wheel_radius_m = (wheel_diameter_inch * 0.0254) / 2

    def calculate_power(self, force, velocity):
        # Mechanische Leistung am Rad
        return force * velocity

    def calculate_torque(self, force):
        # Drehmoment am Rad
        return force * self.wheel_radius_m

    def calculate_motor_current(self, torque):
        # Sicherheits-Check für die Division
        if self.motor_constant <= 0:
            raise ValueError("Die Motorkonstante muss groesser als 0 sein.")

        # Stromstärke
        current = torque / self.motor_constant

        # Falls das Drehmoment negativ ist
        if current < 0:
            current = 0

        return current