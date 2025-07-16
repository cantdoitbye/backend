# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to ensure Python doesn't write pyc files and uses unbuffered mode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory to the current directory (where the Dockerfile is located)
WORKDIR /code

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt /code/

# Install dependencies and necessary build packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code
COPY . /code/

# Expose the port your application runs on
EXPOSE 8000

# Command to run Gunicorn with the specified configuration and WSGI application
CMD ["gunicorn", "--access-logfile", "-", "--workers", "3", "--bind", "0.0.0.0:8000", "settings.wsgi:application"]
