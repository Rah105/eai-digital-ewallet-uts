from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Transaction(db.Model):
    __tablename__ = "transactions"   # NAMA TABEL FIXED

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, nullable=False)      # ID wallet dari wallet-service
    user_id = db.Column(db.Integer, nullable=False)        # User ID (owner wallet)
    type = db.Column(db.String(50), nullable=False)        # TOPUP, PAYMENT, TRANSFER, WITHDRAW
    amount = db.Column(db.Float, nullable=False)

    # PENDING → SUCCESS / FAILED
    status = db.Column(
        db.String(50),
        default="PENDING"
    )

    reference_id = db.Column(db.String(100), unique=True, nullable=True)
    description = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "wallet_id": self.wallet_id,
            "user_id": self.user_id,
            "type": self.type,
            "amount": self.amount,
            "status": self.status,
            "reference_id": self.reference_id,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
