# Secure IoT Telemetry Pipeline

## Overview

This project implements a secure, containerized, end-to-end pipeline for ingesting, validating, and analyzing high-volume IoT telemetry data from a fleet of drones. The system is designed with robust security, real-time processing, and quantitative analysis at its core, demonstrating a practical application of data engineering and statistical monitoring.

The pipeline leverages a modern stack:
- **Data Ingestion:** Mosquitto (MQTT) broker with TLS encryption.
- **Data Validation & Streaming:** A FastAPI gateway that subscribes to MQTT, validates incoming data against an Avro schema, and produces it to a Redpanda (Kafka-compatible) topic.
- **Quantitative Analysis:** An anomaly detection service that consumes the validated data stream and uses a statistical model to identify outliers in real-time.
- **Observability:** A full observability stack using Prometheus for metrics collection and Grafana for visualization, including a pre-provisioned dashboard to monitor pipeline health and analytical results.

## Key Quantitative Skills Demonstrated

This project showcases a strong foundation in quantitative analysis and data-driven decision-making. Key skills include:

- **Statistical Modeling:** Applied the **Isolation Forest** algorithm, an unsupervised learning method ideal for high-dimensional, real-time anomaly detection where labeled training data is unavailable.
- **Parameter Tuning:** Selected and justified the `contamination` parameter (set at 5%), representing the assumed proportion of anomalies in the dataset, a critical factor in model sensitivity.
- **Feature Engineering:** Identified and selected seven key telemetry features for the model: `altitude`, `velocity`, `acceleration_x`, `acceleration_y`, `acceleration_z`, `battery_level`, and `signal_strength`.
- **Quantitative Monitoring:** Implemented and tracked key performance indicators (KPIs) for the pipeline, including:
  - **End-to-End Latency:** Measured as a histogram, tracking the time from data generation to analysis.
  - **Anomaly Rate:** Monitored the percentage of messages flagged as anomalous.
  - **Data Throughput:** Counted messages consumed and processed per second.
- **Statistical Significance:** The anomaly detection model provides a clear, statistically-grounded method for flagging unusual drone behavior, moving beyond simple threshold-based alerts.

## Methodology

### 1. Data Ingestion and Validation

Telemetry data is published to an MQTT broker over a TLS-encrypted connection. A Python-based **Gateway** service subscribes to the `iot/telemetry` topic. Upon receipt, each message is rigorously validated against a predefined **Avro schema** (`drone_telemetry.avsc`). This ensures data integrity and structural consistency before it enters the core processing pipeline. Valid messages are then published to the `telemetry-validated` Kafka topic on a Redpanda broker.

### 2. Real-Time Anomaly Detection

The **Anomaly Detector** service consumes validated telemetry from the Kafka topic. The quantitative core of this service is the **Isolation Forest** algorithm, chosen for several key reasons:

- **Efficiency:** It is computationally efficient and has a low memory footprint, making it ideal for streaming applications.
- **No Labeled Data Required:** As an unsupervised algorithm, it does not require a pre-labeled dataset of "normal" vs. "anomalous" behavior, which is often impractical to obtain in real-world IoT scenarios.
- **High-Dimensional Data:** It performs well on high-dimensional datasets like the one used here (7 features).

The model is initially trained on a buffer of **200 data points**. The `contamination` parameter is set to **0.05**, a domain-specific estimate that assumes approximately 5% of the telemetry readings may be anomalous. This parameter directly influences the model's sensitivity to outliers.

### 3. Quantitative Results and Monitoring

The pipeline's performance and the results of the anomaly detection are quantified and visualized in real-time.

- **Performance Metrics:** The system exposes key metrics via a Prometheus endpoint, which are visualized in a Grafana dashboard. These include:
  - **End-to-End Latency:** The `pipeline_end_to_end_latency_seconds` histogram provides a statistical distribution of data processing times, allowing for the monitoring of performance degradation.
  - **Messages Processed:** The `anomaly_detector_messages_consumed` counter tracks the volume of data being analyzed.
- **Analytical Results:** 
  - **Anomalies Detected:** The `anomaly_detector_anomalies_detected` counter provides a real-time tally of outliers identified by the Isolation Forest model. This raw count, when compared to the total messages consumed, yields a quantifiable **anomaly rate**, a critical KPI for monitoring the overall health of the drone fleet.

This quantitative approach allows an operator to move from reactive troubleshooting to proactive, data-driven maintenance and operational oversight.

## Project Structure

```
.
├─ anomaly_detector/         # PyOD consumer for anomalies
├─ gateway/                  # FastAPI MQTT->Kafka, Avro validation
├─ simulator/                # Telemetry publisher to MQTT
├─ schemas/                  # Avro schema(s)
├─ mosquitto/                # MQTT broker config + runtime dirs
├─ grafana-provisioning/     # Datasource + dashboard provisioning
├─ prometheus/               # Prometheus scrape config
├─ docs/                     # Project docs (planning, notes)
├─ docker-compose.yml        # Orchestration
├─ ca.crt                    # Dev CA (server-side TLS for MQTT)
├─ mqtt.crt, mqtt.key        # Dev MQTT server cert/key (TLS)
└─ README.md                 # You are here
```

## Quick Start

**Prerequisites:**
- Docker Desktop running (Windows/macOS/Linux).

**Run the full stack:**
```bash
docker compose up --build -d
```

**Check services:**
```bash
docker compose ps
```

**Tail logs to see data processing:**
```bash
docker compose logs -f gateway anomaly-detector simulator
```

**Stop the stack:**
```bash
docker compose down
```

## Interacting With The Pipeline

- **Grafana Dashboard:** [http://localhost:3000](http://localhost:3000) (admin/admin) - *This is the primary interface for viewing quantitative results.*
- **Prometheus UI:** [http://localhost:9090](http://localhost:9090)
- **Gateway (FastAPI Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)

To publish a sample message and see it processed:
```bash
docker compose exec mqtt \
  mosquitto_pub -h mqtt -p 1883 -t iot/telemetry \
  -m '{
        "timestamp": 1725446400000,
        "drone_id": "dev",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "altitude": 120.5,
        "velocity": 12.3,
        "acceleration_x": 0.1,
        "acceleration_y": -0.2,
        "acceleration_z": 0.0,
        "battery_level": 87.5,
        "signal_strength": -67.0
      }'
```

## Security

- **Transport Layer Security (TLS):** The MQTT broker is configured to use TLS for encrypted communication.
- **Development vs. Production:** The included certificates are for development purposes only. For a production environment, you should generate your own certificates and consider enabling mutual TLS (mTLS) by setting `require_certificate true` in `mosquitto.conf` and providing client certificates.

## Local Development

You can run each service locally. For example, to run the gateway:
```bash
cd gateway
python -m venv .venv
# On Windows
.\.venv\Scripts\activate
# On macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```