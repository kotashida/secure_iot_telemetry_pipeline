import json
import logging
import os
import time

import fastavro
import paho.mqtt.client as mqtt
from fastapi import FastAPI, Response
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "iot/telemetry"
MQTT_CAFILE = os.getenv("MQTT_CAFILE")
MQTT_TLS_INSECURE = os.getenv("MQTT_TLS_INSECURE", "false").lower() == "true"

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:29092")
KAFKA_TOPIC = "telemetry-validated"

SCHEMA_PATH = "/app/schemas/drone_telemetry.avsc"

# --- Globals ---
app = FastAPI(title="MQTT to Kafka Gateway")
mqtt_client = mqtt.Client()
kafka_producer = None
telemetry_schema = None

# --- Metrics ---
MQTT_MESSAGES_RECEIVED = Counter('gateway_mqtt_messages_received', 'MQTT messages received by gateway')
VALIDATION_SUCCESS = Counter('gateway_validation_success', 'Messages passing Avro validation')
VALIDATION_ERRORS = Counter('gateway_validation_errors', 'Messages failing Avro validation or decode')
KAFKA_MESSAGES_PRODUCED = Counter('gateway_kafka_messages_produced', 'Messages produced to Kafka')
PROCESS_DURATION_SECONDS = Histogram('gateway_process_duration_seconds', 'Processing time per MQTT message in gateway')

# --- Avro Schema Loading ---
def load_schema():
    """Loads the Avro schema from the specified file."""
    global telemetry_schema
    try:
        with open(SCHEMA_PATH, "r") as f:
            telemetry_schema = fastavro.parse_schema(json.load(f))
        logger.info(f"Successfully loaded Avro schema from {SCHEMA_PATH}")
    except FileNotFoundError:
        logger.error(f"Schema file not found at {SCHEMA_PATH}. Exiting.")
        exit(1)

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT, return code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received from MQTT."""
    start = time.perf_counter()
    MQTT_MESSAGES_RECEIVED.inc()
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        # Validate against Avro schema
        fastavro.validate(payload, telemetry_schema)
        VALIDATION_SUCCESS.inc()

        # Forward to Kafka
        if kafka_producer:
            kafka_producer.send(KAFKA_TOPIC, value=payload)
            KAFKA_MESSAGES_PRODUCED.inc()
            logger.info(f"Validated and forwarded message from {payload.get('drone_id','unknown')}")

    except json.JSONDecodeError:
        VALIDATION_ERRORS.inc()
        logger.warning(f"Could not decode JSON from message: {msg.payload}")
    except fastavro.validation.ValidationError as e:
        VALIDATION_ERRORS.inc()
        logger.warning(f"Schema validation failed for message. Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in on_message: {e}")
    finally:
        PROCESS_DURATION_SECONDS.observe(time.perf_counter() - start)

# --- FastAPI Events ---
@app.on_event("startup")
def startup_event():
    """Handles application startup logic."""
    global kafka_producer
    
    load_schema()

    # Init Kafka Producer
    logger.info("Initializing Kafka producer...")
    try:
        kafka_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )
        logger.info(f"Kafka producer connected to {KAFKA_BROKER}")
    except NoBrokersAvailable:
        logger.error(f"Could not connect to any Kafka brokers at {KAFKA_BROKER}. Please check the configuration.")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka producer: {e}")

    # Init MQTT Client
    logger.info("Initializing MQTT client...")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        if MQTT_CAFILE:
            mqtt_client.tls_set(ca_certs=MQTT_CAFILE)
            mqtt_client.tls_insecure_set(MQTT_TLS_INSECURE)
            logger.info("Configured MQTT TLS with provided CA file.")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        logger.error(f"Failed to start MQTT client: {e}")

@app.on_event("shutdown")
def shutdown_event():
    """Handles application shutdown logic."""
    logger.info("Shutting down...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    if kafka_producer:
        kafka_producer.flush()
        kafka_producer.close()
    logger.info("Shutdown complete.")

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Gateway is running"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
