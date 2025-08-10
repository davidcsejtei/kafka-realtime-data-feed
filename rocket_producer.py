import json
import time
import math
import random
from datetime import datetime, timezone
from kafka import KafkaProducer

class RocketTelemetrySimulator:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=["localhost:9092"],
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        
        # Rocket physical parameters
        self.rocket_id = "Falcon-9-001"
        self.dry_mass = 22200  # kg (empty rocket mass)
        self.fuel_mass = 411000  # kg (initial fuel mass)
        self.current_fuel = self.fuel_mass
        self.thrust = 7607000  # N (thrust at sea level)
        self.specific_impulse = 282  # seconds (efficiency of engine)
        self.burn_rate = 2500  # kg/s (fuel consumption rate)
        
        # Current state
        self.altitude = 0  # meters
        self.velocity = 0  # m/s
        self.acceleration = 0  # m/s^2
        self.pitch = 90  # degrees (90 = straight up)
        self.yaw = 0  # degrees
        self.roll = 0  # degrees
        self.mission_time = 0  # seconds
        self.stage = 1  # current stage
        
        # Anomaly system
        self.anomalies = []
        self.anomaly_active = False
        self.engine_efficiency = 1.0  # 1.0 = 100% efficiency
        self.fuel_leak_rate = 0  # additional fuel loss per second
        self.guidance_error = 0  # degrees of guidance system error
        self.sensor_noise = 1.0  # multiplier for sensor noise
        self.engine_throttle = 1.0  # engine throttle setting
        
        # Constants
        self.gravity = 9.81  # m/s^2
        self.air_density_sea_level = 1.225  # kg/m^3
        self.drag_coefficient = 0.3
        self.cross_sectional_area = 10.5  # m^2
        
        print(f"🚀 Rocket {self.rocket_id} initialized for liftoff simulation")
        print(f"Initial fuel: {self.fuel_mass:,.0f} kg")
        print(f"Dry mass: {self.dry_mass:,.0f} kg")
        
    def calculate_air_density(self, altitude):
        """Calculate air density at given altitude using exponential model"""
        return self.air_density_sea_level * math.exp(-altitude / 8400)
    
    def calculate_drag_force(self):
        """Calculate drag force based on current velocity and altitude"""
        if self.velocity <= 0:
            return 0
        air_density = self.calculate_air_density(self.altitude)
        return 0.5 * air_density * self.velocity**2 * self.drag_coefficient * self.cross_sectional_area
    
    def check_for_anomalies(self):
        """Randomly trigger rocket anomalies"""
        # Only check for new anomalies if none are currently active
        if not self.anomaly_active and random.random() < 0.008:  # 0.8% chance per second
            anomaly_type = random.choice([
                "engine_underperformance",
                "fuel_leak", 
                "guidance_failure",
                "sensor_malfunction",
                "engine_shutdown",
                "attitude_control_loss",
                "thermal_anomaly",
                "structural_vibration"
            ])
            
            self.trigger_anomaly(anomaly_type)
    
    def trigger_anomaly(self, anomaly_type):
        """Trigger a specific anomaly"""
        self.anomaly_active = True
        duration = random.uniform(5, 30)  # Anomaly lasts 5-30 seconds
        
        anomaly_data = {
            "type": anomaly_type,
            "start_time": self.mission_time,
            "duration": duration,
            "severity": random.choice(["minor", "moderate", "critical"])
        }
        
        if anomaly_type == "engine_underperformance":
            self.engine_efficiency = random.uniform(0.4, 0.8)
            anomaly_data["description"] = f"Engine performing at {self.engine_efficiency*100:.0f}% efficiency"
            
        elif anomaly_type == "fuel_leak":
            self.fuel_leak_rate = random.uniform(50, 200)  # kg/s additional loss
            anomaly_data["description"] = f"Fuel leak detected: {self.fuel_leak_rate:.0f} kg/s additional consumption"
            
        elif anomaly_type == "guidance_failure":
            self.guidance_error = random.uniform(2, 8)
            anomaly_data["description"] = f"Guidance system error: ±{self.guidance_error:.1f}° deviation"
            
        elif anomaly_type == "sensor_malfunction":
            self.sensor_noise = random.uniform(1.5, 3.0)
            anomaly_data["description"] = f"Sensor readings showing {self.sensor_noise*100-100:.0f}% increased noise"
            
        elif anomaly_type == "engine_shutdown":
            self.engine_throttle = 0.0
            duration = random.uniform(3, 8)  # Shorter duration for engine shutdown
            anomaly_data["duration"] = duration
            anomaly_data["description"] = "Emergency engine shutdown activated"
            anomaly_data["severity"] = "critical"
            
        elif anomaly_type == "attitude_control_loss":
            anomaly_data["description"] = "Attitude control system malfunction - erratic movements"
            
        elif anomaly_type == "thermal_anomaly":
            anomaly_data["description"] = "Thermal protection system anomaly detected"
            
        elif anomaly_type == "structural_vibration":
            anomaly_data["description"] = "Abnormal structural vibrations detected"
        
        self.anomalies.append(anomaly_data)
    
    def update_anomalies(self):
        """Update active anomalies and resolve expired ones"""
        active_anomalies = []
        resolved_any = False
        
        for anomaly in self.anomalies:
            if self.mission_time - anomaly["start_time"] < anomaly["duration"]:
                active_anomalies.append(anomaly)
            else:
                # Anomaly resolved - no console output
                
                # Reset parameters based on anomaly type
                if anomaly["type"] == "engine_underperformance":
                    self.engine_efficiency = 1.0
                elif anomaly["type"] == "fuel_leak":
                    self.fuel_leak_rate = 0
                elif anomaly["type"] == "guidance_failure":
                    self.guidance_error = 0
                elif anomaly["type"] == "sensor_malfunction":
                    self.sensor_noise = 1.0
                elif anomaly["type"] == "engine_shutdown":
                    self.engine_throttle = 1.0
        
        self.anomalies = active_anomalies
        self.anomaly_active = len(active_anomalies) > 0
    
    def update_physics(self, dt=1.0):
        """Update rocket physics for next time step"""
        # Check for new anomalies
        self.check_for_anomalies()
        self.update_anomalies()
        
        if self.current_fuel <= 0:
            # No more fuel, coast phase
            net_force = -self.drag_force - (self.dry_mass * self.gravity)
            self.acceleration = net_force / self.dry_mass
        else:
            # Active burn phase with anomaly effects
            base_fuel_consumed = self.burn_rate * dt
            fuel_leak_loss = self.fuel_leak_rate * dt
            total_fuel_consumed = min(base_fuel_consumed + fuel_leak_loss, self.current_fuel)
            self.current_fuel -= total_fuel_consumed
            
            current_mass = self.dry_mass + self.current_fuel
            
            # Apply engine efficiency and throttle
            thrust_force = self.thrust * self.engine_efficiency * self.engine_throttle
            weight = current_mass * self.gravity
            self.drag_force = self.calculate_drag_force()
            
            # Net force calculation
            net_force = thrust_force - weight - self.drag_force
            self.acceleration = net_force / current_mass
        
        # Update velocity and altitude
        self.velocity += self.acceleration * dt
        self.altitude += self.velocity * dt
        
        # Gravity turn - realistic pitch program with guidance errors
        if self.mission_time > 10 and self.altitude > 1000:
            # Start gravity turn after 10 seconds and 1km altitude
            target_pitch = 90 - (self.mission_time - 10) * 0.8
            target_pitch = max(target_pitch, 45)  # Don't go below 45 degrees initially
            # Apply guidance error
            self.pitch = target_pitch + random.uniform(-self.guidance_error, self.guidance_error)
        
        # Small attitude adjustments for realism + anomaly effects
        base_yaw_change = random.uniform(-0.5, 0.5) if self.mission_time > 20 else 0
        base_roll_change = random.uniform(-0.2, 0.2)
        
        # Apply attitude control anomalies
        attitude_multiplier = 1.0
        for anomaly in self.anomalies:
            if anomaly["type"] == "attitude_control_loss":
                attitude_multiplier = 5.0  # Much more erratic movement
        
        self.yaw += base_yaw_change * attitude_multiplier
        self.roll += base_roll_change * attitude_multiplier
        
        # Keep angles in reasonable bounds
        self.yaw = max(-5, min(5, self.yaw))
        self.roll = max(-10, min(10, self.roll))
        
        self.mission_time += dt
    
    def get_engine_temperature(self):
        """Calculate realistic engine temperature with anomaly effects"""
        if self.current_fuel <= 0:
            # Cooling down
            base_temp = max(800, 3200 - (self.mission_time * 20))
        else:
            # Active burn
            base_temp = 3200
            variation = random.uniform(-50, 50)
            base_temp += variation
        
        # Apply thermal anomaly effects
        for anomaly in self.anomalies:
            if anomaly["type"] == "thermal_anomaly":
                base_temp += random.uniform(200, 800)  # Dangerous temperature spike
        
        return base_temp
    
    def get_rocket_status(self):
        """Determine current rocket status"""
        if self.current_fuel <= 0:
            if self.velocity > 0:
                return "coasting"
            else:
                return "descent"
        elif self.mission_time < 3:
            return "ignition"
        elif self.altitude < 1000:
            return "liftoff"
        else:
            return "ascent"
    
    def apply_sensor_noise(self, value, noise_factor=1.0):
        """Apply sensor noise to readings"""
        noise = random.uniform(-0.02, 0.02) * noise_factor * self.sensor_noise
        return value * (1 + noise)
    
    def generate_telemetry(self):
        """Generate realistic telemetry data with potential anomalies"""
        fuel_percentage = (self.current_fuel / self.fuel_mass) * 100
        
        # Add vibration effects to sensor readings
        vibration_factor = 1.0
        for anomaly in self.anomalies:
            if anomaly["type"] == "structural_vibration":
                vibration_factor = 3.0
        
        telemetry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "rocketId": self.rocket_id,
            "missionTime": round(self.mission_time, 1),
            "stage": self.stage,
            "status": self.get_rocket_status(),
            
            # Position and motion (with sensor noise)
            "altitude": round(self.apply_sensor_noise(self.altitude, vibration_factor), 1),
            "velocity": round(self.apply_sensor_noise(self.velocity, vibration_factor), 1),
            "acceleration": round(self.apply_sensor_noise(self.acceleration, vibration_factor), 2),
            "machNumber": round(self.velocity / 343, 2),
            
            # Attitude (with potential guidance errors and noise)
            "pitch": round(self.apply_sensor_noise(self.pitch), 1),
            "yaw": round(self.apply_sensor_noise(self.yaw), 1),
            "roll": round(self.apply_sensor_noise(self.roll), 1),
            
            # Propulsion
            "fuelRemaining": round(fuel_percentage, 1),
            "fuelMass": round(self.current_fuel, 0),
            "thrust": round(self.thrust * self.engine_efficiency * self.engine_throttle) if self.current_fuel > 0 else 0,
            "burnRate": round(self.burn_rate + self.fuel_leak_rate, 1) if self.current_fuel > 0 else 0,
            "engineEfficiency": round(self.engine_efficiency * 100, 1),
            
            # Environmental
            "engineTemp": round(self.get_engine_temperature(), 0),
            "airDensity": round(self.calculate_air_density(self.altitude), 6),
            "dragForce": round(self.drag_force, 0),
            
            # Calculated values
            "totalMass": round(self.dry_mass + self.current_fuel, 0),
            "thrustToWeight": round(self.thrust * self.engine_efficiency * self.engine_throttle / ((self.dry_mass + self.current_fuel) * self.gravity), 2) if self.current_fuel > 0 else 0,
            "apogee": round(self.altitude + (self.velocity**2) / (2 * self.gravity), 0) if self.velocity > 0 else self.altitude,
            
            # System health indicators (for anomaly detection)
            "sensorNoise": round(self.sensor_noise, 2),
            "guidanceError": round(self.guidance_error, 2),
            "fuelLeakRate": round(self.fuel_leak_rate, 1),
            "activeAnomalies": len(self.anomalies)
        }
        
        return telemetry
    
    def run_simulation(self):
        """Run the telemetry simulation"""
        try:
            print("\n🚀 Starting rocket liftoff simulation...")
            print("Press Ctrl+C to stop\n")
            
            while True:
                # Update physics
                self.update_physics(1.0)
                
                # Generate and send telemetry
                telemetry = self.generate_telemetry()
                self.producer.send("rocket-telemetry", value=telemetry)
                
                # Console output with key metrics
                status_emoji = {
                    "ignition": "🔥",
                    "liftoff": "🚀",
                    "ascent": "⬆️",
                    "coasting": "🛰️",
                    "descent": "⬇️"
                }.get(telemetry["status"], "📡")
                
                print(f"{status_emoji} T+{telemetry['missionTime']:>6.1f}s | "
                      f"Alt: {telemetry['altitude']:>8.0f}m | "
                      f"Vel: {telemetry['velocity']:>6.0f}m/s | "
                      f"Fuel: {telemetry['fuelRemaining']:>5.1f}% | "
                      f"Status: {telemetry['status']}")
                
                # Stop simulation if rocket reaches very high altitude or crashes
                if self.altitude > 100000 or (self.altitude <= 0 and self.mission_time > 10):
                    print(f"\n🎯 Simulation ended at T+{self.mission_time:.1f}s")
                    if self.altitude > 100000:
                        print(f"🌌 Rocket reached space! Final altitude: {self.altitude:,.0f}m")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Simulation stopped at T+{self.mission_time:.1f}s")
            print(f"Final altitude: {self.altitude:,.0f}m")
            print(f"Final velocity: {self.velocity:,.0f}m/s")
        finally:
            self.producer.close()

if __name__ == "__main__":
    simulator = RocketTelemetrySimulator()
    simulator.run_simulation()