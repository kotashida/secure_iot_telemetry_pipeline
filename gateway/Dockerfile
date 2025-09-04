# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the local schemas directory into the container
COPY schemas /app/schemas

# Copy CA certificate for MQTT TLS (development)
COPY ca.crt /app/certs/ca.crt

# Copy the rest of the application's code
COPY gateway/ .

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
