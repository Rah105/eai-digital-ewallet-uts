import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

# Create instance/ folder if not exists
os.makedirs(INSTANCE_DIR, exist_ok=True)


class Config:
    # === APP KEY ===
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    # === DATABASE ===
    DB_NAME = os.getenv("DB_NAME", "service.db")
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(INSTANCE_DIR, DB_NAME)}"
    )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === SERVICE INFO ===
    SERVICE_NAME = os.getenv("SERVICE_NAME", "generic-service")

    # Default port = 3000 (set beda di tiap service)
    PORT = int(os.getenv("PORT", 3000))

    # === CORS ===
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
