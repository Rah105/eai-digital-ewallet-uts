from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from models import db, Wallet
from config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
CORS(app)

api = Api(
    app,
    version="1.0",
    title="Wallet Service API",
    description="Handles user wallet balance, top-ups, and payments",
    doc="/api-docs/"
)

wallet_ns = api.namespace("wallets", description="Wallet operations")


# ============================
#     SWAGGER MODELS
# ============================
wallet_model = api.model("Wallet", {
    "id": fields.Integer(readOnly=True),
    "user_id": fields.Integer(required=True),
    "balance": fields.Float(),
    "status": fields.String(),
    "created_at": fields.String(),
    "updated_at": fields.String(),
})

topup_model = api.model("Topup", {
    "user_id": fields.Integer(required=True),
    "amount": fields.Float(required=True)
})

deduct_model = api.model("Deduct", {
    "user_id": fields.Integer(required=True),
    "amount": fields.Float(required=True)
})


# ============================
#         ENDPOINTS
# ============================

@wallet_ns.route("/")
class WalletList(Resource):

    @wallet_ns.doc("list_all_wallets")
    @wallet_ns.marshal_list_with(wallet_model)
    def get(self):
        """Get all wallets"""
        wallets = Wallet.query.all()
        return wallets


    @wallet_ns.doc("create_wallet")
    @wallet_ns.expect(wallet_model)
    @wallet_ns.marshal_with(wallet_model, code=201)
    def post(self):
        """Create new wallet"""
        data = request.json
        new_wallet = Wallet(
            user_id=data["user_id"],
            balance=data.get("balance", 0.0),
            status=data.get("status", "ACTIVE")
        )
        db.session.add(new_wallet)
        db.session.commit()
        return new_wallet, 201


@wallet_ns.route("/<int:user_id>")
@wallet_ns.param("user_id", "User ID associated with the wallet")
class WalletByUser(Resource):

    @wallet_ns.doc("get_wallet_by_user")
    @wallet_ns.marshal_with(wallet_model)
    def get(self, user_id):
        """Get wallet by user_id"""
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            api.abort(404, "Wallet not found")
        return wallet


@wallet_ns.route("/topup")
class WalletTopup(Resource):

    @wallet_ns.doc("topup_wallet")
    @wallet_ns.expect(topup_model)
    def post(self):
        """Top-up Wallet"""
        data = request.json
        wallet = Wallet.query.filter_by(user_id=data["user_id"]).first()

        if not wallet:
            api.abort(404, "Wallet not found")

        wallet.balance += data["amount"]
        wallet.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "message": "Top-up successful",
            "user_id": wallet.user_id,
            "new_balance": wallet.balance
        })


@wallet_ns.route("/deduct")
class WalletDeduct(Resource):

    @wallet_ns.doc("deduct_wallet_balance")
    @wallet_ns.expect(deduct_model)
    def post(self):
        """Deduct balance for payments"""
        data = request.json
        wallet = Wallet.query.filter_by(user_id=data["user_id"]).first()

        if not wallet:
            api.abort(404, "Wallet not found")

        if wallet.balance < data["amount"]:
            api.abort(400, "Insufficient balance")

        wallet.balance -= data["amount"]
        wallet.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "message": "Balance deduction successful",
            "user_id": wallet.user_id,
            "new_balance": wallet.balance
        })


# ================
#  INTERNAL API
# ================
@app.route("/internal/wallets/<int:user_id>")
def get_wallet_internal(user_id):
    wallet = Wallet.query.filter_by(user_id=user_id).first()
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404
    return jsonify(wallet.to_dict())


# ================
#  HEALTH CHECK
# ================
@app.route("/health")
def health_check():
    return jsonify({
        "service": Config.SERVICE_NAME,
        "status": "running"
    })


# ================
#  AUTO DB CREATE
# ================
@app.cli.command("create-db")
def create_db():
    with app.app_context():
        db.create_all()
        print("Wallet database created!")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)