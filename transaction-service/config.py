import os
from dotenv import load_dotenv

load_dotenv()

# Direktori utama project
basedir = os.path.abspath(os.path.dirname(__file__))

# Folder instance (tempat database SQLite)
instance_path = os.path.join(basedir, "instance")

# Buat folder instance jika belum ada
os.makedirs(instance_path, exist_ok=True)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "user-service-secret")

    # Database SQLite disimpan di instance/
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(instance_path, 'user.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Konfigurasi port dan service name
    PORT = int(os.getenv("PORT", 3001))
    SERVICE_NAME = os.getenv("SERVICE_NAME", "user-service")

    # URL Service lain (opsional digunakan untuk integrasi)
    TRANSACTION_SERVICE_URL = os.getenv("TRANSACTION_SERVICE_URL", "http://localhost:3002")
    NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:3003")
