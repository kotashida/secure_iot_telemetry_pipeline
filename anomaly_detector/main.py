import json
import logging
import os
import time

import pandas as pd
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from pyod.models.iforest import IForest
from prometheus_client import Counter, Histogram, start_http_server

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:29092")
KAFKA_TOPIC = "telemetry-validated"
GROUP_ID = "anomaly-detector-group"

# Model and Data Configuration
FEATURES = [
    'altitude', 'velocity', 'acceleration_x', 'acceleration_y',
    'acceleration_z', 'battery_level', 'signal_strength'
]
TRAINING_SAMPLES = 200
CONTAMINATION = 0.05

# --- Globals ---
consumer = None
model = None
data_buffer = []

# --- Metrics ---
MESSAGES_CONSUMED = Counter('anomaly_detector_messages_consumed', 'Messages consumed from Kafka')
ANOMALIES_DETECTED = Counter('anomaly_detector_anomalies_detected', 'Anomalies detected by Isolation Forest')
END_TO_END_LATENCY_SECONDS = Histogram(
    'pipeline_end_to_end_latency_seconds',
    'End-to-end latency from publish (timestamp) to detection',
)

def initialize_consumer():
    """Initializes the Kafka consumer, retrying until successful."""
    global consumer
    while consumer is None:
        try:
            logger.info(f"Attempting to connect to Kafka at {KAFKA_BROKER}...")
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BROKER,
                auto_offset_reset='earliest',
                group_id=GROUP_ID,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            )
            logger.info(f"Successfully connected to Kafka!")
        except NoBrokersAvailable:
            logger.error(f"Could not connect to any Kafka brokers at {KAFKA_BROKER}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def main():
    """Main function to run the anomaly detection service."""
    global model
    global data_buffer

    # Start Prometheus metrics HTTP server
    metrics_port = int(os.getenv("METRICS_PORT", "9000"))
    start_http_server(metrics_port)
    logger.info(f"Metrics server started on :{metrics_port} (/metrics)")
    initialize_consumer()

    logger.info("Starting anomaly detection service...")
    logger.info(f"Waiting for {TRAINING_SAMPLES} messages to train initial model...")

    for message in consumer:
        try:
            data = message.value
            MESSAGES_CONSUMED.inc()

            # Latency measurement (ms timestamp in payload)
            if 'timestamp' in data:
                now_ms = int(time.time() * 1000)
                dt_seconds = max(0, (now_ms - int(data['timestamp'])) / 1000.0)
                END_TO_END_LATENCY_SECONDS.observe(dt_seconds)

            feature_vector = [data[f] for f in FEATURES]

            # Collect training data
            if model is None:
                data_buffer.append(feature_vector)
                if len(data_buffer) < TRAINING_SAMPLES:
                    if len(data_buffer) % 25 == 0:
                        logger.info(f"Collected {len(data_buffer)} training messages...")
                    continue
                # Train initial model
                try:
                    df = pd.DataFrame(data_buffer, columns=FEATURES)
                    model = IForest(contamination=CONTAMINATION, random_state=42)
                    model.fit(df)
                    logger.info("Isolation Forest model trained with initial buffer.")
                except Exception as e:
                    logger.error(f"Failed to train model: {e}")
                    data_buffer = []
                    model = None
                    continue

            # Predict using trained model
            try:
                prediction = int(model.predict([feature_vector])[0])  # 1 = outlier, 0 = inlier
                if prediction == 1:
                    ANOMALIES_DETECTED.inc()
                    logger.warning(f"Anomaly detected for drone_id={data.get('drone_id','unknown')}")
            except Exception as e:
                logger.error(f"Prediction failed: {e}")

        except json.JSONDecodeError:
            logger.error("Failed to decode message from Kafka.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Service stopped by user.")
    finally:
        if consumer:
            consumer.close()
        logger.info("Kafka consumer closed. Exiting.")
