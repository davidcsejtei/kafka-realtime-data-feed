import json
import time
import math
from datetime import datetime
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
    
    def update_physics(self, dt=1.0):
        """Update rocket physics for next time step"""
        if self.current_fuel <= 0:
            # No more fuel, coast phase
            net_force = -self.drag_force - (self.dry_mass * self.gravity)
            self.acceleration = net_force / self.dry_mass
        else:
            # Active burn phase
            fuel_consumed = min(self.burn_rate * dt, self.current_fuel)
            self.current_fuel -= fuel_consumed
            
            current_mass = self.dry_mass + self.current_fuel
            thrust_force = self.thrust
            weight = current_mass * self.gravity
            self.drag_force = self.calculate_drag_force()
            
            # Net force calculation
            net_force = thrust_force - weight - self.drag_force
            self.acceleration = net_force / current_mass
        
        # Update velocity and altitude
        self.velocity += self.acceleration * dt
        self.altitude += self.velocity * dt
        
        # Gravity turn - realistic pitch program
        if self.mission_time > 10 and self.altitude > 1000:
            # Start gravity turn after 10 seconds and 1km altitude
            target_pitch = 90 - (self.mission_time - 10) * 0.8
            target_pitch = max(target_pitch, 45)  # Don't go below 45 degrees initially
            self.pitch = target_pitch
        
        # Small attitude adjustments for realism
        self.yaw += (random.uniform(-0.5, 0.5) if self.mission_time > 20 else 0)
        self.roll += random.uniform(-0.2, 0.2)
        
        # Keep angles in reasonable bounds
        self.yaw = max(-5, min(5, self.yaw))
        self.roll = max(-10, min(10, self.roll))
        
        self.mission_time += dt
    
    def get_engine_temperature(self):
        """Calculate realistic engine temperature based on burn time"""
        if self.current_fuel <= 0:
            # Cooling down
            return max(800, 3200 - (self.mission_time * 20))
        else:
            # Active burn
            base_temp = 3200
            variation = random.uniform(-50, 50)
            return base_temp + variation
    
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
    
    def generate_telemetry(self):
        """Generate realistic telemetry data"""
        fuel_percentage = (self.current_fuel / self.fuel_mass) * 100
        
        telemetry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "rocketId": self.rocket_id,
            "missionTime": round(self.mission_time, 1),
            "stage": self.stage,
            "status": self.get_rocket_status(),
            
            # Position and motion
            "altitude": round(self.altitude, 1),
            "velocity": round(self.velocity, 1),
            "acceleration": round(self.acceleration, 2),
            "machNumber": round(self.velocity / 343, 2),  # Speed of sound at sea level
            
            # Attitude
            "pitch": round(self.pitch, 1),
            "yaw": round(self.yaw, 1),
            "roll": round(self.roll, 1),
            
            # Propulsion
            "fuelRemaining": round(fuel_percentage, 1),
            "fuelMass": round(self.current_fuel, 0),
            "thrust": self.thrust if self.current_fuel > 0 else 0,
            "burnRate": self.burn_rate if self.current_fuel > 0 else 0,
            
            # Environmental
            "engineTemp": round(self.get_engine_temperature(), 0),
            "airDensity": round(self.calculate_air_density(self.altitude), 6),
            "dragForce": round(self.drag_force, 0),
            
            # Calculated values
            "totalMass": round(self.dry_mass + self.current_fuel, 0),
            "thrustToWeight": round(self.thrust / ((self.dry_mass + self.current_fuel) * self.gravity), 2) if self.current_fuel > 0 else 0,
            "apogee": round(self.altitude + (self.velocity**2) / (2 * self.gravity), 0) if self.velocity > 0 else self.altitude
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
    import random
    
    simulator = RocketTelemetrySimulator()
    simulator.run_simulation()