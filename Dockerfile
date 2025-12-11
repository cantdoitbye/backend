# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_RETRIES=5

# Set the working directory
WORKDIR /code

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt /code/

# Install dependencies with timeout handling
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev && \
    pip install --upgrade pip && \
    pip install --no-cache-dir --timeout 1000 --retries 5 -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code
COPY . /code/

# Create settings symlink if it doesn't exist
RUN ln -sf settings/base.py settings.py || true

# Expose the port
EXPOSE 8000

# Command to run Daphne (ASGI server for WebSocket support)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "socialooumph.asgi:application"]