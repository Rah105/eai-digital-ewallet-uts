import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'notification-service-secret')

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///notification.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PORT = int(os.getenv('PORT', 3003))
    SERVICE_NAME = os.getenv('SERVICE_NAME', 'notification-service')

    # URL Service lain (optional)
    USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:3001')
