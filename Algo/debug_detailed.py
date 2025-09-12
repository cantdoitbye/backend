#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

print('=== Testing settings execution step by step ===')

try:
    print('1. Importing pathlib and os...')
    from pathlib import Path
    import os
    print('✓ Basic imports successful')
    
    print('2. Testing django-environ...')
    import environ
    print('✓ django-environ imported')
    
    print('3. Testing structlog...')
    import structlog
    print('✓ structlog imported')
    
    print('4. Setting BASE_DIR...')
    BASE_DIR = Path(__file__).parent
    print(f'✓ BASE_DIR: {BASE_DIR}')
    
    print('5. Creating environ.Env...')
    env = environ.Env(
        DEBUG=(bool, True),
        SECRET_KEY=(str, 'django-insecure-dev-key-change-in-production-abc123xyz789'),
        DATABASE_URL=(str, 'sqlite:///db.sqlite3'),
        REDIS_URL=(str, 'redis://localhost:6379/0'),
        ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    )
    print('✓ environ.Env created')
    
    print('6. Testing env file read...')
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        environ.Env.read_env(env_file)
        print('✓ .env file read')
    else:
        print('✓ No .env file found (using defaults)')
    
    print('7. Getting environment variables...')
    SECRET_KEY = env('SECRET_KEY')
    DEBUG = env('DEBUG')
    print(f'✓ SECRET_KEY length: {len(SECRET_KEY)}')
    print(f'✓ DEBUG: {DEBUG}')
    
    print('8. Testing database config...')
    DATABASES = {
        'default': env.db()
    }
    print(f'✓ Database config: {DATABASES["default"]["ENGINE"]}')
    
except Exception as e:
    print(f'✗ Error at step: {e}')
    import traceback
    traceback.print_exc()

print('\n=== Now testing full settings module ===')
try:
    # Set the environment variable that Django expects
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph_feed.settings')
    
    # Try to read the settings file content directly
    settings_path = BASE_DIR / 'ooumph_feed' / 'settings.py'
    print(f'Reading settings from: {settings_path}')
    
    # Execute the settings file in a controlled way
    settings_globals = {}
    settings_locals = {}
    
    with open(settings_path, 'r') as f:
        settings_content = f.read()
    
    exec(settings_content, settings_globals, settings_locals)
    
    print('\n✓ Settings executed successfully!')
    print(f'DJANGO_APPS: {len(settings_locals.get("DJANGO_APPS", []))}')
    print(f'THIRD_PARTY_APPS: {len(settings_locals.get("THIRD_PARTY_APPS", []))}')
    print(f'LOCAL_APPS: {len(settings_locals.get("LOCAL_APPS", []))}')
    print(f'INSTALLED_APPS: {len(settings_locals.get("INSTALLED_APPS", []))}')
    
except Exception as e:
    print(f'✗ Error executing settings: {e}')
    import traceback
    traceback.print_exc()
