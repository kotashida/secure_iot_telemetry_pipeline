# Secure IoT Telemetry Pipeline

A containerized, end-to-end pipeline for ingesting, validating, streaming, and analyzing IoT (drone) telemetry with security and observability built in. The stack uses MQTT for ingestion, a FastAPI gateway for validation and Kafka/Redpanda production, a PyOD-based anomaly detector, and Prometheus/Grafana for metrics.

## Overview

- MQTT broker (`mqtt`): Receives telemetry on topic `iot/telemetry`.
- Gateway (`gateway`): Subscribes to MQTT, validates messages against Avro (`schemas/drone_telemetry.avsc`), publishes valid events to Kafka topic `telemetry-validated` on Redpanda.
- Anomaly Detector (`anomaly-detector`): Consumes `telemetry-validated` and flags anomalies using Isolation Forest (PyOD), exports Prometheus metrics.
- Simulator (`simulator`): Generates/sample-publishes telemetry to MQTT.
- Redpanda (`redpanda`): Kafka-compatible broker.
- Prometheus/Grafana: Observability stack and pre-provisioned dashboard.

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

Removed unnecessary development artifacts (client and unused Redpanda certs, CSRs). Runtime broker data/logs are now ignored by Git.

## Quick Start

Prerequisites:
- Docker Desktop running (Windows/macOS/Linux).

Run the full stack:
```
docker compose up --build -d
```

Check services:
```
docker compose ps
```

Tail logs (processing view):
```
docker compose logs -f gateway anomaly-detector simulator
```

Stop the stack:
```
docker compose down
```

## Interacting With The Pipeline

- MQTT topic: `iot/telemetry`
- Kafka topic: `telemetry-validated`
- Avro schema: `schemas/drone_telemetry.avsc`

Publish a sample message (from inside the MQTT container, avoids host tooling):
```
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

Open UIs:
- Gateway (FastAPI docs): http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin default)
- Prometheus: http://localhost:9090

## Configuration

Environment variables (set via `docker-compose.yml`):
- `MQTT_BROKER`, `MQTT_PORT`, `MQTT_CAFILE`, `MQTT_TLS_INSECURE`
- `KAFKA_BROKER`
- `METRICS_PORT` (anomaly-detector)

Update TLS:
- Mosquitto TLS listener uses `ca.crt`, `mqtt.crt`, `mqtt.key` mounted into the broker.
- For development, anonymous connections are allowed and clients set `MQTT_TLS_INSECURE=true`.
- To enable mTLS, set `require_certificate true` in `mosquitto/config/mosquitto.conf` and provide client certs; update services accordingly.

## Local Development (per service)

Gateway:
```
cd gateway
python -m venv .venv
./.venv/Scripts/activate  # Windows; use `source .venv/bin/activate` on Linux/macOS
pip install -r requirements.txt
uvicorn main:app --reload
```

Simulator:
```
cd simulator
python -m venv .venv
./.venv/Scripts/activate
pip install -r requirements.txt
python main.py
```

## Testing

- Framework: `pytest` (run within each service after installing dev deps)
```
pytest -q
```
- Targets: Avro validation (gateway), Kafka/MQTT integration (mock where possible), anomaly detection logic.

## Troubleshooting

- Compose warning `version is obsolete`: safe to ignore; can remove the `version` key.
- No telemetry seen: check `simulator` logs; ensure MQTT `1883` is reachable and `gateway` is Up.
- Kafka issues: ensure `redpanda` status is Healthy; view logs with `docker compose logs -f redpanda`.

## Security Notes

- Dev certificates are included only for local use.
- Private keys/CSRs are excluded via `.gitignore`.
- To harden: disable anonymous MQTT, enable mTLS, and secure Kafka with TLS before deploying beyond local.

