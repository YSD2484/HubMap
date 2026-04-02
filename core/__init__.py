import os
from core.config import settings

# Automatically configure environment variables required globally
os.environ["FOUNDER_DATA_BQ_CREDENTIALS"] = settings.FOUNDER_DATA_BQ_CREDENTIALS
