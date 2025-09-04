# Repository Guidelines

## Project Structure & Module Organization
- `gateway/`: FastAPI service bridging MQTT -> Kafka (Redpanda). Loads Avro from `schemas/drone_telemetry.avsc`. Env: `MQTT_BROKER`, `MQTT_PORT`, `KAFKA_BROKER`.
- `anomaly_detector/`: Kafka consumer using PyOD Isolation Forest on topic `telemetry-validated`.
- `simulator/`: Publishes sample telemetry to MQTT topic `iot/telemetry`.
- `schemas/`: Avro schemas for validated telemetry.
- `mosquitto/`: MQTT broker config (1883, non-TLS) plus data/log dirs.
- `docker-compose.yml`: Orchestrates Mosquitto, Redpanda, Gateway, Anomaly Detector, Simulator.

## Build, Test, and Development Commands
- Run full stack: `docker-compose up --build` (add `-d` to detach). Stop: `docker-compose down`.
- View logs: `docker-compose logs -f gateway` (or any service name).
- Local gateway dev: `cd gateway && python -m venv .venv && .\\.venv\\Scripts\\activate && pip install -r requirements.txt && uvicorn main:app --reload`.
- Local simulator: `cd simulator && python -m venv .venv && .\\.venv\\Scripts\\activate && pip install -r requirements.txt && python main.py`.
- Quick publish (requires mosquitto-clients): `mosquitto_pub -h localhost -p 1883 -t iot/telemetry -m '{"drone_id":"dev","timestamp":0,...}'` (must match Avro schema fields).

## Coding Style & Naming Conventions
- Python 3.9+, 4-space indent, PEP 8; prefer type hints and docstrings.
- Files/modules: `snake_case`; classes: `PascalCase`; constants: `UPPER_CASE`.
- Topics: MQTT `iot/telemetry`; Kafka `telemetry-validated`. Keep names lowercase, hyphen/underscore separated.

## Testing Guidelines
- Framework: `pytest`. Place tests under `tests/` as `test_*.py` per service (e.g., `gateway/tests/test_validation.py`).
- Targets: validate Avro schema handling, MQTT/Kafka integration (mock where possible). Aim >= 80% coverage on changed code.
- Run: `pytest -q` (from service root after installing dev deps).

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`). Keep messages imperative and scoped.
- PRs: clear description, linked issues, how-to-validate steps (compose commands), and relevant logs/screenshots. Keep changes focused per service.

## Security & Configuration Tips
- Do not commit production secrets. Root cert/key files are for local development only.
- Configure via env vars; optionally use a `.env` and `env_file` in Compose. If enabling TLS, update Mosquitto/Redpanda configs and client settings consistently.
