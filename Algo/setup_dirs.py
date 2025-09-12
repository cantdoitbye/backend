# Create necessary directories
import os
from pathlib import Path

# Ensure all required directories exist
BASE_DIR = Path(__file__).resolve().parent

# Create directories if they don't exist
dirs_to_create = [
    BASE_DIR / 'static',
    BASE_DIR / 'media', 
    BASE_DIR / 'staticfiles',
    BASE_DIR / 'logs',
    BASE_DIR / 'templates',
    BASE_DIR / 'templates' / 'analytics_dashboard'
]

for dir_path in dirs_to_create:
    dir_path.mkdir(exist_ok=True)
    print(f"Created directory: {dir_path}")

print("All directories created successfully!")
