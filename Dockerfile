# Use a lightweight Python base image
FROM python:3.11-slim

# Install Tesseract OCR and clean up to keep the container small
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port Gunicorn runs on
EXPOSE 10000

# Start Gunicorn with memory-recycling constraints
# --workers 1: Limits the application to a single process container to save baseline RAM
# --threads 2: Uses lightweight threads to handle I/O without duplicating the Python process space
# --max-requests 10: Automatically restarts the worker after 10 requests to wipe out memory leaks
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "--threads", "2", "--max-requests", "10", "--timeout", "120", "app:app"]
