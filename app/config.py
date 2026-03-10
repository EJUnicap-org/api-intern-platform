"""Application configuration settings."""
import os

# Environment settings
IS_PRODUCTION = os.getenv("ENV", "development") == "production"

# Database
DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost:5432/ej_unicap_db"

# Redis
REDIS_URL = "redis://localhost:6379/0"

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")  # Change in production
