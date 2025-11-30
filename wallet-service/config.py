import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "wallet-dev-secret-key")
    
    # SQLite auto-create di local folder wallet-service
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///wallet.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Port default untuk Wallet Service
    PORT = int(os.getenv("PORT", 3004))
    SERVICE_NAME = "wallet-service"

    # URL external (User Service)
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:3001")