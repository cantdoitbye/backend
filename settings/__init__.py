import os
import logging
from pathlib import Path

ENV = os.getenv('ENV', 'development')

logger = logging.getLogger('environment')
logger.info(f"Running in {ENV} environment")

if ENV == 'production':
    from .production import *
elif ENV == 'local':
    from .local import *
else:
    from .development import *
