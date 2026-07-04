class Motor:
    def __init__(self, wheel_diameter_inch=27, motor_constant=1.5):
        self.wheel_diameter_inch = wheel_diameter_inch
        self.motor_constant = motor_constant  # Nm/A
        self.wheel_radius_m = (wheel_diameter_inch * 0.0254) / 2

    def calculate_power(self, force, velocity):
        return force * velocity

    def calculate_torque(self, force):
        return force * self.wheel_radius_m

    def calculate_motor_current(self, torque):
        if self.motor_constant <= 0:
            raise ValueError("Motorkonstante muss größer als 0 sein.")

        current = torque / self.motor_constant

        if current < 0:
            current = 0

        return current