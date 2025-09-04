# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY simulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY simulator/ .

# Copy CA certificate for MQTT TLS (development)
COPY ca.crt /app/certs/ca.crt

# Command to run the application
CMD ["python", "main.py"]
