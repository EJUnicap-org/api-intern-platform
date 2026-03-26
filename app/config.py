"""Application configuration settings."""
import os

# Environment settings
IS_PRODUCTION = os.getenv("ENV", "development") == "production"

# Database
DATABASE_URL = os.getenv("DATABASE_URL") #"postgresql+asyncpg://postgres:root@localhost:5432/ej_unicap_db"

# Redis
REDIS_URL = "redis://localhost:6379/0"

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "473a140aa31f2a63af7c5caabbde18045ee71803035257c9e9f443fac857980f")  # Change in production
