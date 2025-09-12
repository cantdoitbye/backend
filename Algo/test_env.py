import os
import environ
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent

print(f"BASE_DIR: {BASE_DIR}")
print(f".env file exists: {(BASE_DIR / '.env').exists()}")

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'django-insecure-change-in-production'),
    DATABASE_URL=(str, 'postgres://user:pass@localhost:5432/ooumph_feed'),
    REDIS_URL=(str, 'redis://localhost:6379/0'),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read environment file
if (BASE_DIR / '.env').exists():
    print("Reading .env file...")
    environ.Env.read_env(BASE_DIR / '.env')
    print("Environment file read successfully")
else:
    print("No .env file found")

print(f"SECRET_KEY from env: {env('SECRET_KEY')}")
print(f"DEBUG from env: {env('DEBUG')}")
print(f"ALLOWED_HOSTS from env: {env('ALLOWED_HOSTS')}")
