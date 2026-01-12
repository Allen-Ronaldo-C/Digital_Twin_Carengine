import time
import random
import json
from datetime import datetime
from dataclasses import dataclass, asdict
import numpy as np

@dataclass
class SimulatedSensor:
    name: str
    value: float
    min_value: float
    max_value: float
    noise_level: float = 0.1

    def read(self) -> dict:
        noise = random.uniform(-self.noise_level, self.noise_level)
        value = np.clip(self.value + noise, self.min_value, self.max_value)
        return {
            'command': self.name,
            'value': round(value, 2),
            'unit': self.get_unit(),
            'timestamp': datetime.now().isoformat()
        }

    def get_unit(self):
        units = {
            'RPM': 'rpm',
            'SPEED': 'km/h',
            'COOLANT_TEMP': '°C',
            'ENGINE_LOAD': '%',
            'THROTTLE_POS': '%',
            'INTAKE_TEMP': '°C',
            'MAF': 'g/s',
            'FUEL_RATE': 'L/h',
            'OIL_TEMP': '°C',
            'OIL_PRESSURE': 'psi'
        }
        return units.get(self.name, '')

class VirtualCarSimulator:
    def __init__(self):
        self.sensors = {
            'RPM': SimulatedSensor('RPM', 800, 0, 7000, 50),
            'SPEED': SimulatedSensor('SPEED', 0, 0, 200, 2),
            'COOLANT_TEMP': SimulatedSensor('COOLANT_TEMP', 85, 60, 120, 1),
            'ENGINE_LOAD': SimulatedSensor('ENGINE_LOAD', 20, 0, 100, 2),
            'THROTTLE_POS': SimulatedSensor('THROTTLE_POS', 15, 0, 100, 1),
            'INTAKE_TEMP': SimulatedSensor('INTAKE_TEMP', 25, 20, 80, 0.5),
            'MAF': SimulatedSensor('MAF', 5, 0, 200, 0.5),
            'FUEL_RATE': SimulatedSensor('FUEL_RATE', 0.8, 0, 20, 0.1),
            'OIL_TEMP': SimulatedSensor('OIL_TEMP', 80, 60, 120, 1),
            'OIL_PRESSURE': SimulatedSensor('OIL_PRESSURE', 40, 15, 80, 2)
        }
        self.throttle = 0
        self.gear = 3
        self.mileage = 45230.0
    def set_throttle(self, throttle: float):
        self.throttle = np.clip(throttle, 0, 100)
        self._update_sensors()
    def set_gear(self, gear: int):
        self.gear = np.clip(gear, 1, 6)
        self._update_sensors()
    def _update_sensors(self):
        target_rpm = 800 + (self.throttle * 50)
        self.sensors['RPM'].value += (target_rpm - self.sensors['RPM'].value) * 0.1
        gear_ratios = [0, 3.5, 2.5, 1.8, 1.3, 1.0, 0.8]
        speed = (self.sensors['RPM'].value * gear_ratios[self.gear]) / 60
        self.sensors['SPEED'].value = speed
        self.sensors['ENGINE_LOAD'].value = self.throttle * 0.7
        heat_gen = (self.sensors['RPM'].value / 1000) * 0.2 + self.throttle * 0.05
        cooling = (self.sensors['COOLANT_TEMP'].value - 85) * 0.1
        self.sensors['COOLANT_TEMP'].value += heat_gen - cooling
        temp_diff = self.sensors['COOLANT_TEMP'].value - self.sensors['OIL_TEMP'].value
        self.sensors['OIL_TEMP'].value += temp_diff * 0.05
        base_pressure = (self.sensors['RPM'].value / 1000) * 8 + 20
        temp_factor = 1.0 - ((self.sensors['OIL_TEMP'].value - 80) / 200)
        self.sensors['OIL_PRESSURE'].value = base_pressure * np.clip(temp_factor, 0.5, 1.5)
        fuel = ((self.throttle / 100) * 12 + (self.sensors['RPM'].value / 1000) * 0.8)
        self.sensors['FUEL_RATE'].value = fuel
        if self.sensors['SPEED'].value > 0:
            self.mileage += self.sensors['SPEED'].value / 3600
    def read_all_sensors(self) -> dict:
        return {name: sensor.read() for name, sensor in self.sensors.items()}
    def get_status_summary(self) -> str:
        """Get human-readable status"""
        rpm = self.sensors['RPM'].value
        speed = self.sensors['SPEED'].value
        temp = self.sensors['COOLANT_TEMP'].value
        oil_pressure = self.sensors['OIL_PRESSURE'].value

        return f"""
╔═══════════════════════════════════════════════════╗
║          VIRTUAL CAR STATUS                       ║
╠═══════════════════════════════════════════════════╣
║ RPM:           {rpm:>6.0f} rpm                    ║
║ Speed:         {speed:>6.1f} km/h                 ║
║ Coolant Temp:  {temp:>6.1f} °C                    ║
║ Oil Pressure:  {oil_pressure:>6.1f} psi           ║
║ Throttle:      {self.throttle:>6.1f} %            ║
║ Gear:          {self.gear:>6d}                    ║
║ Mileage:       {self.mileage:>6.1f} km            ║
╚═══════════════════════════════════════════════════╝
        """


class DigitalTwinTester:
    def __init__(self):
        self.car = VirtualCarSimulator()
        self.history = []
    def test_idle(self, duration=5):
        print("\n TEST 1: Idle Engine")
        print("=" * 50)
        self.car.set_throttle(0)
        for i in range(duration):
            data = self.car.read_all_sensors()
            self.history.append(data)
            print(f"Second {i + 1}: RPM={data['RPM']['value']}, Temp={data['COOLANT_TEMP']['value']:.1f}°C")
            time.sleep(1)
    def test_acceleration(self, duration=10):
        print("\n TEST 2: Acceleration")
        print("=" * 50)
        for i in range(duration):
            throttle = min(100, i * 10)
            self.car.set_throttle(throttle)
            data = self.car.read_all_sensors()
            self.history.append(data)
            print(
                f"Second {i + 1}: Throttle={throttle}%, RPM={data['RPM']['value']:.0f}, Speed={data['SPEED']['value']:.1f} km/h")
            time.sleep(1)
    def test_steady_cruise(self, duration=10):
        print("\n TEST 3: Steady Cruise")
        print("=" * 50)
        self.car.set_throttle(50)
        self.car.set_gear(5)
        for i in range(duration):
            data = self.car.read_all_sensors()
            self.history.append(data)
            print(
                f"Second {i + 1}: Speed={data['SPEED']['value']:.1f} km/h, Temp={data['COOLANT_TEMP']['value']:.1f}°C, Fuel={data['FUEL_RATE']['value']:.2f} L/h")
            time.sleep(1)
    def test_high_load(self, duration=8):
        print("\n TEST 4: High Load (Stress Test)")
        print("=" * 50)
        self.car.set_throttle(90)
        self.car.set_gear(3)
        for i in range(duration):
            data = self.car.read_all_sensors()
            self.history.append(data)
            warnings = []
            if data['COOLANT_TEMP']['value'] > 100:
                warnings.append("⚠️  HIGH TEMP")
            if data['RPM']['value'] > 6000:
                warnings.append("⚠️  HIGH RPM")
            warn_str = " ".join(warnings) if warnings else "✓ OK"
            print(
                f"Second {i + 1}: Load={data['ENGINE_LOAD']['value']:.1f}%, Temp={data['COOLANT_TEMP']['value']:.1f}°C, {warn_str}")
            time.sleep(1)
    def analyze_health(self):
        print("\n HEALTH ANALYSIS")
        print("=" * 50)
        if not self.history:
            print("No data collected")
            return
        temps = [d['COOLANT_TEMP']['value'] for d in self.history]
        rpms = [d['RPM']['value'] for d in self.history]
        oil_pressures = [d['OIL_PRESSURE']['value'] for d in self.history]
        avg_temp = np.mean(temps)
        max_temp = np.max(temps)
        avg_rpm = np.mean(rpms)
        max_rpm = np.max(rpms)
        min_oil_pressure = np.min(oil_pressures)
        print(f"Average Temperature:  {avg_temp:.1f}°C")
        print(f"Maximum Temperature:  {max_temp:.1f}°C")
        print(f"Average RPM:          {avg_rpm:.0f}")
        print(f"Maximum RPM:          {max_rpm:.0f}")
        print(f"Minimum Oil Pressure: {min_oil_pressure:.1f} psi")
        print("\n HEALTH SCORES:")
        cooling_score = max(0, 100 - abs(avg_temp - 85) * 5)
        print(f"Cooling System:       {cooling_score:.1f}% {'✓' if cooling_score > 80 else '⚠️'}")
        lub_score = max(0, 100 - max(0, 25 - min_oil_pressure) * 4)
        print(f"Lubrication System:   {lub_score:.1f}% {'✓' if lub_score > 80 else '⚠️'}")
        overall = (cooling_score + lub_score) / 2
        print(f"Overall Health:       {overall:.1f}%")
        if overall > 90:
            risk = "LOW"
        elif overall > 75:
            risk = "MEDIUM"
        else:
            risk = "HIGH"
        print(f"\nFailure Risk:         {risk}")
    def predict_maintenance(self):
        print("\n MAINTENANCE PREDICTIONS")
        print("=" * 50)
        current_mileage = self.car.mileage
        maintenance = {
            'Oil Change': (5000, 43000),
            'Spark Plugs': (50000, 30000),
            'Air Filter': (20000, 40000),
            'Coolant Flush': (40000, 35000),
            'Timing Belt': (100000, 50000)
        }
        for item, (interval, last_service) in maintenance.items():
            miles_since = current_mileage - last_service
            remaining = interval - miles_since
            status = "✓" if remaining > interval * 0.2 else "⚠️"
            print(f"{item:20} Due in: {remaining:>8.0f} km {status}")
    def export_data(self, filename='digital_twin_test_data.json'):
        print(f"\n💾 Exporting data to {filename}")
        export = {
            'test_timestamp': datetime.now().isoformat(),
            'vehicle_id': 'TEST_VEHICLE_001',
            'mileage': self.car.mileage,
            'sensor_history': self.history
        }
        with open(filename, 'w') as f:
            json.dump(export, f, indent=2)

        print(f"✓ Exported {len(self.history)} data points")

    def run_full_test_suite(self):
        print("\n" + "=" * 50)
        print(" DIGITAL TWIN TESTING SUITE")
        print("=" * 50)

        self.test_idle(duration=5)
        time.sleep(1)

        self.test_acceleration(duration=10)
        time.sleep(1)

        self.test_steady_cruise(duration=10)
        time.sleep(1)

        self.test_high_load(duration=8)
        time.sleep(1)

        print(self.car.get_status_summary())

        self.analyze_health()
        self.predict_maintenance()
        self.export_data()

        print("\n" + "=" * 50)
        print(" TEST SUITE COMPLETE")
        print("=" * 50)


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║  Digital Twin Testing & Simulation Environment             ║
║  --------------------------------------------------        ║
║  This script simulates a car engine for testing            ║
║  your digital twin implementation without real hardware    ║
╚════════════════════════════════════════════════════════════╝
    """)

    tester = DigitalTwinTester()

    try:
        tester.run_full_test_suite()
    except KeyboardInterrupt:
        print("\n\n  Test interrupted by user")

    print("\n Testing complete. Check 'digital_twin_test_data.json' for exported data.\n")


if __name__ == "__main__":
    main()