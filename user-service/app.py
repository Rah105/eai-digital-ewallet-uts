from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from config import Config
from models import db, User
import bcrypt

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
CORS(app)

api = Api(
    app,
    version="1.0",
    title="User Service API",
    description="Handles users, login, roles, and admin operations",
    doc="/api-docs/"
)

user_ns = api.namespace("users", description="User operations")


# ============================
# SWAGGER MODELS
# ============================

user_model = api.model("User", {
    "id": fields.Integer(readOnly=True),
    "name": fields.String(),
    "email": fields.String(),
    "role": fields.String(),
    "status": fields.String(),
})

register_model = api.model("RegisterUser", {
    "name": fields.String(required=True),
    "email": fields.String(required=True),
    "password": fields.String(required=True)
})

login_model = api.model("Login", {
    "email": fields.String(required=True),
    "password": fields.String(required=True)
})

admin_create_model = api.model("AdminCreateUser", {
    "name": fields.String(required=True),
    "email": fields.String(required=True),
    "password": fields.String(required=True),
    "role": fields.String(default="USER"),
    "status": fields.String(default="ACTIVE"),
})


# ============================
# ROLE HELPERS
# ============================

def get_role():
    return request.headers.get("X-Role", None)

def get_user_id():
    return request.headers.get("X-User-ID", None)

def require_admin():
    if get_role() != "ADMIN":
        api.abort(403, "Admin privilege required")

def require_user():
    if get_role() != "USER":
        api.abort(403, "User privilege required")


# ============================
# ENDPOINTS
# ============================

@user_ns.route("/")
class UserList(Resource):

    @user_ns.expect(register_model)
    @user_ns.marshal_with(user_model, code=201)
    def post(self):
        """Register normal user"""
        data = request.json

        hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()

        user = User(
            name=data["name"],
            email=data["email"],
            password=hashed,
            role="USER",
            status="ACTIVE"
        )
        db.session.add(user)
        db.session.commit()
        return user, 201


# ============================
# ADMIN: LIST ALL USERS
# ============================

@user_ns.route("/admin/all")
class AdminUserList(Resource):

    @user_ns.marshal_list_with(user_model)
    def get(self):
        """Admin: View all users"""
        require_admin()
        return User.query.all()


# ============================
# ADMIN: CREATE USER
# ============================

@user_ns.route("/admin-create")
class AdminCreateUser(Resource):

    @user_ns.expect(admin_create_model)
    @user_ns.marshal_with(user_model, code=201)
    def post(self):
        """Admin create user"""
        require_admin()

        data = request.json
        hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()

        user = User(
            name=data["name"],
            email=data["email"],
            password=hashed,
            role=data.get("role", "USER"),
            status=data.get("status", "ACTIVE")
        )

        db.session.add(user)
        db.session.commit()
        return user, 201


# ============================
# ADMIN: GET USER BY ID & DELETE USER
# ============================

@user_ns.route("/admin/<int:user_id>")
class AdminUserDetail(Resource):

    @user_ns.marshal_with(user_model)
    def get(self, user_id):
        """Admin melihat user tertentu"""
        require_admin()
        return User.query.get_or_404(user_id)

    def delete(self, user_id):
        """Admin delete user"""
        require_admin()
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted"}


# ============================
# USER: PROFILE / ME
# ============================

@user_ns.route("/me")
class UserMe(Resource):

    @user_ns.marshal_with(user_model)
    def get(self):
        """User mengambil data dirinya sendiri"""
        require_user()
        user = User.query.get_or_404(get_user_id())
        return user


# ============================
# LOGIN
# ============================

@user_ns.route("/login")
class UserLogin(Resource):

    @user_ns.expect(login_model)
    def post(self):
        """Login for user & admin"""
        data = request.json
        user = User.query.filter_by(email=data["email"]).first()

        if not user:
            api.abort(404, "User not found")

        if not bcrypt.checkpw(data["password"].encode(), user.password.encode()):
            api.abort(401, "Invalid password")

        return {
            "message": "Login successful",
            "user_id": user.id,
            "role": user.role,
            "status": user.status
        }


# ============================
# INTERNAL API (OTHER SERVICES)
# ============================

@app.route("/internal/users/<int:user_id>")
def internal_user(user_id):
    return User.query.get_or_404(user_id).to_dict()


# ============================
# HEALTH CHECK
# ============================

@app.route("/health")
def health():
    return {"service": Config.SERVICE_NAME, "status": "running"}


# ============================
# AUTO CREATE DB
# ============================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✔ User DB Created")
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)
