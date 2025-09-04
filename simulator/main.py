import paho.mqtt.client as mqtt
import json
import time
import random
import uuid
import os
import logging

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "iot/telemetry"
MQTT_CAFILE = os.getenv("MQTT_CAFILE")
MQTT_TLS_INSECURE = os.getenv("MQTT_TLS_INSECURE", "false").lower() == "true"

# Simulator Configuration
DRONE_ID = f"drone-{uuid.uuid4()}"
SIMULATION_INTERVAL_S = 1  # 1 message per second

def create_telemetry_data():
    """Generates a single telemetry data point."""
    return {
        "timestamp": int(time.time() * 1000),
        "drone_id": DRONE_ID,
        "latitude": random.uniform(-90.0, 90.0),
        "longitude": random.uniform(-180.0, 180.0),
        "altitude": random.uniform(0, 1000.0),
        "velocity": random.uniform(0, 100.0),
        "acceleration_x": random.uniform(-10.0, 10.0),
        "acceleration_y": random.uniform(-10.0, 10.0),
        "acceleration_z": random.uniform(-9.8, 15.0), # Includes gravity
        "battery_level": random.uniform(0.0, 100.0),
        "signal_strength": random.uniform(-90.0, -30.0), # in dBm
    }

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT Broker!")
    else:
        logger.error(f"Failed to connect, return code {rc}")

def main():
    """Main function to run the simulator."""
    client = mqtt.Client()
    client.on_connect = on_connect

    try:
        if MQTT_CAFILE:
            client.tls_set(ca_certs=MQTT_CAFILE)
            client.tls_insecure_set(MQTT_TLS_INSECURE)
            logger.info("Configured MQTT TLS with provided CA file.")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except ConnectionRefusedError:
        logger.error(f"Connection to MQTT broker at {MQTT_BROKER}:{MQTT_PORT} refused. Is it running?")
        return
    except Exception as e:
        logger.error(f"An error occurred during connection: {e}")
        return

    client.loop_start()

    logger.info(f"Starting simulation for drone: {DRONE_ID}")
    logger.info(f"Publishing to topic: {MQTT_TOPIC}")

    try:
        while True:
            data = create_telemetry_data()
            payload = json.dumps(data)
            result = client.publish(MQTT_TOPIC, payload)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish message: {mqtt.error_string(result.rc)}")
            else:
                logger.info(f"Published: {payload}")
            time.sleep(SIMULATION_INTERVAL_S)
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
    finally:
        client.loop_stop()
        client.disconnect()
        logger.info("Disconnected from MQTT broker.")

if __name__ == "__main__":
    main()
