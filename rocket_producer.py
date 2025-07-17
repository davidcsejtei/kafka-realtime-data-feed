import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def generate_telemetry():
    return {
        "rocket_id": "Starship",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "altitude_km": round(random.uniform(0, 120), 2),
        "velocity_kmh": round(random.uniform(0, 28000), 2),
        "engine_temp_c": round(random.uniform(200, 1200), 2),
        "fuel_level_percent": round(random.uniform(0, 100), 2),
        "battery_voltage_v": round(random.uniform(24, 30), 2),
        "status": random.choice(["PREFLIGHT", "FLIGHT", "LANDING", "LANDED", "ABORT"])
    }

while True:
    telemetry = generate_telemetry()
    producer.send("rocket-telemetry", value=telemetry)
    print("Sent:", telemetry)
    time.sleep(1)