from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from config import Config
from models import db, Transaction, Wallet
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
CORS(app)

api = Api(
    app,
    version="1.0",
    title="Transaction Service API",
    description="Handles digital wallet transactions (topup, payment, transfer)",
    doc="/api-docs/"
)

transaction_ns = api.namespace("transactions", description="Transaction operations")

# ============================
#   SWAGGER MODELS 
# ============================
transaction_model = api.model("Transaction", {
    "id": fields.Integer(readOnly=True),
    "wallet_id": fields.Integer(required=True),
    "user_id": fields.Integer(required=True),
    "type": fields.String(required=True),
    "amount": fields.Float(required=True),
    "status": fields.String(),
    "reference_id": fields.String(),
    "description": fields.String(),
    "created_at": fields.String(),
    "updated_at": fields.String(),
})

topup_model = api.model("Topup", {
    "wallet_id": fields.Integer(required=True),
    "amount": fields.Float(required=True),
})

payment_model = api.model("Payment", {
    "wallet_id": fields.Integer(required=True),
    "amount": fields.Float(required=True),
    "description": fields.String(required=False),
})

transfer_model = api.model("Transfer", {
    "from_wallet_id": fields.Integer(required=True),
    "to_wallet_id": fields.Integer(required=True),
    "amount": fields.Float(required=True),
})

# ============================
#        ENDPOINTS
# ============================

@transaction_ns.route("/")
class TransactionList(Resource):

    @transaction_ns.marshal_list_with(transaction_model)
    def get(self):
        """Get all transactions"""
        return Transaction.query.all()


# ============================================================
#                    TOPUP ENDPOINT
# ============================================================
@transaction_ns.route("/topup")
class Topup(Resource):

    @transaction_ns.expect(topup_model)
    def post(self):
        """Topup a wallet"""
        data = request.json
        wallet = Wallet.query.get(data["wallet_id"])

        if not wallet:
            return {"error": "Wallet not found"}, 404

        # Tambah saldo
        wallet.balance += data["amount"]

        trx = Transaction(
            wallet_id=wallet.id,
            user_id=wallet.user_id,
            type="TOPUP",
            amount=data["amount"],
            status="SUCCESS",
            description="Topup balance"
        )

        db.session.add(trx)
        db.session.commit()

        return {"message": "Topup successful", "new_balance": wallet.balance}, 200


# ============================================================
#                 PAYMENT ENDPOINT
# ============================================================
@transaction_ns.route("/payment")
class Payment(Resource):

    @transaction_ns.expect(payment_model)
    def post(self):
        """Make a payment (saldo berkurang)"""
        data = request.json
        wallet = Wallet.query.get(data["wallet_id"])

        if not wallet:
            return {"error": "Wallet not found"}, 404

        if wallet.balance < data["amount"]:
            return {"error": "Insufficient balance"}, 400

        # Kurangi saldo
        wallet.balance -= data["amount"]

        trx = Transaction(
            wallet_id=wallet.id,
            user_id=wallet.user_id,
            type="PAYMENT",
            amount=data["amount"],
            status="SUCCESS",
            description=data.get("description", "Payment done")
        )

        db.session.add(trx)
        db.session.commit()

        return {"message": "Payment successful", "new_balance": wallet.balance}, 200


# ============================================================
#                 TRANSFER ENDPOINT
# ============================================================
@transaction_ns.route("/transfer")
class Transfer(Resource):

    @transaction_ns.expect(transfer_model)
    def post(self):
        """Transfer money between wallets"""
        data = request.json

        from_wallet = Wallet.query.get(data["from_wallet_id"])
        to_wallet = Wallet.query.get(data["to_wallet_id"])

        if not from_wallet or not to_wallet:
            return {"error": "One or both wallets not found"}, 404

        if from_wallet.balance < data["amount"]:
            return {"error": "Insufficient balance"}, 400

        from_wallet.balance -= data["amount"]
        to_wallet.balance += data["amount"]

        trx = Transaction(
            wallet_id=from_wallet.id,
            user_id=from_wallet.user_id,
            type="TRANSFER",
            amount=data["amount"],
            status="SUCCESS",
            description=f"Transfer to wallet {to_wallet.id}"
        )

        db.session.add(trx)
        db.session.commit()

        return {
            "message": "Transfer successful",
            "from_wallet_balance": from_wallet.balance,
            "to_wallet_balance": to_wallet.balance
        }, 200


# ============================================================
# INTERNAL API
# ============================================================
@app.route("/internal/transactions/<int:user_id>")
def get_transactions_internal(user_id):
    trxs = Transaction.query.filter_by(user_id=user_id).all()
    return jsonify([t.to_dict() for t in trxs])


# HEALTH CHECK
@app.route("/health")
def health_check():
    return jsonify({
        "service": Config.SERVICE_NAME,
        "status": "running"
    })


# AUTO DB CREATE
@app.cli.command("create-db")
def create_db():
    with app.app_context():
        db.create_all()
        print("Transaction DB created!")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)
