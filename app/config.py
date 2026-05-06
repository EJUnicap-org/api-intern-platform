"""Application configuration settings."""
import os

# Environment settings
IS_PRODUCTION = os.getenv("ENV", "development") == "production"

# Database
DATABASE_URL = os.getenv("DATABASE_URL") #"postgresql+asyncpg://postgres:root@localhost:5432/ej_unicap_db"

# Redis #nao vai ser usado agora
#REDIS_URL = "redis://localhost:6379/0"

# Security
SECRET_KEY = os.getenv("JWT_SECRET")  
