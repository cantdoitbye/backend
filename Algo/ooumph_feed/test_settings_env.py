import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
print(f"BASE_DIR in settings context: {BASE_DIR}")
print(f".env file path: {BASE_DIR / '.env'}")
print(f".env file exists: {(BASE_DIR / '.env').exists()}")

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'fallback-secret-key'),
    DATABASE_URL=(str, 'postgres://user:pass@localhost:5432/ooumph_feed'),
    REDIS_URL=(str, 'redis://localhost:6379/0'),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read environment file
env_file = BASE_DIR / '.env'
if env_file.exists():
    print("Reading .env file from settings context...")
    environ.Env.read_env(env_file)
    print("Successfully read .env file")
else:
    print("No .env file found in settings context")

# Test env access
try:
    secret_key = env('SECRET_KEY')
    print(f"SECRET_KEY from env in settings context: {secret_key}")
except Exception as e:
    print(f"Error reading SECRET_KEY: {e}")

try:
    debug = env('DEBUG')
    print(f"DEBUG from env in settings context: {debug}")
except Exception as e:
    print(f"Error reading DEBUG: {e}")
