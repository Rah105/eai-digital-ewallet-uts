from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"  # FIX: harus pakai __tablename__

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # Password hashed
    password = db.Column(db.String(255), nullable=False)

    # NEW: Role untuk membedakan admin dan user
    role = db.Column(db.String(20), default="USER")  # USER / ADMIN

    status = db.Column(db.String(20), default="ACTIVE")

    # E-Wallet balance (support transaksi & topup)
    balance = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------
    # PASSWORD HANDLING
    # --------------------------
    def set_password(self, plain_password):
        """Hash password sebelum disimpan"""
        hashed = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt())
        self.password = hashed.decode()

    def check_password(self, plain_password):
        """Cek kecocokan password"""
        return bcrypt.checkpw(plain_password.encode(), self.password.encode())

    # --------------------------
    # SERIALIZER (AMANKAN PASSWORD)
    # --------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "balance": self.balance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
