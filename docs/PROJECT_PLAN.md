# Project Plan: Secure IoT Telemetry Pipeline

### 1. Vision & Scope

*   **Vision:** To build a robust, secure, and observable data pipeline for real-time IoT telemetry data, using a simulated drone as the data source.
*   **Core Problem:** IoT data streams are often vulnerable, unreliable, and difficult to monitor. This project addresses these challenges by implementing end-to-end security, schema validation, and real-time anomaly detection.
*   **End Goal:** A containerized, multi-service application that can ingest, process, and analyze simulated drone sensor data, meeting specific performance and accuracy targets.

### 2. Stack & Technologies

*   **Data Simulation:** Python script simulating a drone's sensor outputs (GPS, accelerometer, gyroscope).
*   **Ingestion Protocol:** **MQTT** for lightweight, low-latency data publishing.
*   **Gateway & Validation:** **FastAPI** service to subscribe to MQTT, validate data against a schema, and produce to the data stream.
*   **Data Streaming:** **Kafka** (or **Redpanda** for a simpler, compatible alternative) for a durable, high-throughput message bus.
*   **Schema Enforcement:** **Avro** (or Protobuf) for strongly-typed, evolvable data schemas.
*   **Security:** **TLS/mTLS** to secure data in transit between all services.
*   **Anomaly Detection:** **PyOD** (specifically **Isolation Forest**) running in a dedicated Python service.
*   **Observability:** **Prometheus** for metrics collection and **Grafana** for visualization and dashboarding.
*   **Containerization:** **Docker Compose** to define, build, and run the entire multi-service application.

### 3. Measurable Outcomes (Success Criteria)

*   **Reliability:** **99.9%** message delivery from simulator to anomaly detector, tested under simulated backpressure (e.g., consumer slowdown).
*   **Latency:** **P95 end-to-end latency < 250ms** (from MQTT publish to anomaly detection processing).
*   **Accuracy:** Anomaly detection F1-score ≥ 0.85 on a pre-labeled set of simulated sensor faults.

---

### Development Phases

**Phase 1: Foundation & Core Pipeline Setup**

*   **Task 1: Project Scaffolding:**
    *   Initialize a Git repository with a `.gitignore` file.
    *   Create the directory structure (`/simulator`, `/gateway`, `/anomaly_detector`, `/schemas`, `/certs`, `/grafana-provisioning`).
*   **Task 2: Basic Docker Compose:**
    *   Set up an initial `docker-compose.yml` with services for an MQTT broker (e.g., `eclipse-mosquitto`) and Redpanda/Kafka.
*   **Task 3: Data Schema Definition:**
    *   Define the `drone_telemetry.avsc` Avro schema. Include fields like `timestamp`, `drone_id`, `latitude`, `longitude`, `altitude`, `velocity`, `acceleration_x`, `acceleration_y`, `acceleration_z`.
*   **Task 4: Drone Simulator v1:**
    *   Create a Python script that generates data according to the Avro schema and publishes it as JSON to the MQTT broker.

**Phase 2: Gateway & Stream Integration**

*   **Task 1: FastAPI Gateway v1:**
    *   Develop a FastAPI application that subscribes to the MQTT topic.
    *   On message receipt, it will validate the data against the Avro schema.
    *   Upon successful validation, it produces the message to a `telemetry-validated` Kafka topic.
    *   Containerize the gateway and add it to `docker-compose.yml`.

**Phase 3: Anomaly Detection Service**

*   **Task 1: Anomaly Detector v1:**
    *   Create a Python service that consumes messages from the `telemetry-validated` Kafka topic.
    *   Implement a basic Isolation Forest model using PyOD.
    *   For now, simply print detected anomalies to the console ("Anomaly detected in message from drone_id: ...").
    *   Containerize the service and add it to `docker-compose.yml`.

**Phase 4: Security Hardening (TLS/mTLS)**

*   **Task 1: Generate Certificates:**
    *   Create a script to generate self-signed CA, server, and client certificates for all services.
*   **Task 2: Secure MQTT:**
    *   Configure the Mosquitto broker to require TLS for all connections.
    *   Update the simulator and gateway to connect to MQTT using TLS.
*   **Task 3: Secure Kafka/Redpanda:**
    *   Configure the broker to use TLS for internal and external communication.
    *   Update the gateway and anomaly detector to use TLS when connecting to Kafka.
*   **Task 4 (Optional Stretch):** Implement mTLS for client verification between services.

**Phase 5: Observability & Metrics**

*   **Task 1: Instrument Services:**
    *   Add Prometheus client libraries to the FastAPI gateway and the anomaly detector.
    *   Expose a `/metrics` endpoint on each service.
    *   Metrics to add:
        *   `gateway`: Messages received, messages validated, messages produced, validation errors.
        *   `anomaly_detector`: Messages consumed, anomalies detected.
        *   Add latency tracking (e.g., using histograms).
*   **Task 2: Prometheus & Grafana Setup:**
    *   Add Prometheus and Grafana services to `docker-compose.yml`.
    *   Configure `prometheus.yml` to scrape the metrics endpoints of the gateway and anomaly detector.
*   **Task 3: Build Dashboards:**
    *   Create a Grafana dashboard to visualize key metrics: message throughput, end-to-end latency (P95, P99), anomaly rate, and error counts.

**Phase 6: Benchmarking & Validation**

*   **Task 1: Latency & Reliability Testing:**
    *   Enhance the simulator to add a `publish_timestamp` to each message.
    *   Measure latency in the anomaly detector service.
    *   Create a load-testing script to simulate backpressure and verify message delivery rates.
*   **Task 2: Anomaly Accuracy Testing:**
    *   Enhance the simulator to generate a labeled dataset with known faults (e.g., sudden sensor spikes, data freezes).
    *   Run this dataset through the pipeline and log the anomaly detector's predictions.
    *   Write a script to compare predictions against the ground-truth labels and calculate the F1-score.
*   **Task 3: Refinement:**
    *   Tune the Isolation Forest model, Kafka partitions, or service resources based on test results to meet the measurable outcomes.
