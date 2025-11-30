# frontend/app.py
import os
import requests
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------
# Config
# ------------------------------------------------------
TEMPLATE_FOLDER = os.getenv("TEMPLATE_FOLDER", "templates")
STATIC_FOLDER = os.getenv("STATIC_FOLDER", "static")
app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)

app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
API_GATEWAY = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
REQUEST_TIMEOUT = float(os.getenv("API_REQUEST_TIMEOUT", "20"))

# ------------------------------------------------------
# Helpers
# ------------------------------------------------------
def _safe_json(res):
    try:
        text = res.text.strip()
        if not text:
            return {"error": "Empty response from upstream", "status_code": res.status_code}
        return res.json()
    except Exception:
        return {
            "error": f"Invalid JSON from upstream: {res.text[:200]}",
            "status_code": getattr(res, "status_code", None)
        }

def api_get(endpoint, token=None):
    url = f"{API_GATEWAY}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        return _safe_json(res)
    except requests.exceptions.Timeout:
        flash("⏱ Request ke API Gateway timeout.", "warning")
    except requests.exceptions.ConnectionError:
        flash("🚫 Tidak dapat terhubung ke API Gateway.", "danger")
    except Exception as e:
        flash(f"⚠ Error: {e}", "danger")
    return []

def api_post(endpoint, payload=None, token=None):
    url = f"{API_GATEWAY}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        res = requests.post(url, json=payload or {}, headers=headers, timeout=REQUEST_TIMEOUT)
        return _safe_json(res), res.status_code
    except requests.exceptions.Timeout:
        return {"error": "Request to API Gateway timed out"}, 504
    except requests.exceptions.ConnectionError:
        return {"error": "API Gateway unreachable"}, 503
    except Exception as e:
        return {"error": str(e)}, 500

def api_delete(endpoint, token=None):
    url = f"{API_GATEWAY}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        res = requests.delete(url, headers=headers, timeout=REQUEST_TIMEOUT)
        return _safe_json(res), res.status_code
    except Exception as e:
        return {"error": str(e)}, 500

# ------------------------------------------------------
# Auth Helper
# ------------------------------------------------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("access_token"):
            flash("⚠ Please login first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

# ------------------------------------------------------
# AUTH ROUTES
# ------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        payload = {
            "full_name": request.form.get("full_name"),
            "email": request.form.get("email"),
            "password": request.form.get("password")
        }
        resp, status = api_post("/auth/register", payload)

        if status in (200, 201):
            flash("✅ Registrasi berhasil. Silakan login.", "success")
            return redirect(url_for("login"))

        flash(f"❌ {resp.get('error', 'Gagal registrasi')}", "danger")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        resp, status = api_post("/auth/login", {
            "email": request.form.get("email"),
            "password": request.form.get("password")
        })

        if status == 200 and resp.get("access_token"):
            session["access_token"] = resp["access_token"]
            session["user"] = resp.get("user")
            return redirect(url_for("dashboard"))

        flash(f"❌ {resp.get('error', 'Invalid credentials')}", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("👋 Logout berhasil.", "info")
    return redirect(url_for("login"))

# ------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------
@app.route("/")
def home():
    if not session.get("access_token"):
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    token = session["access_token"]
    user = session["user"]

    transactions = api_get("/transactions", token) or []
    notifications = api_get("/notifications", token) or []
    reports = api_get("/reports", token) or []
    users = api_get("/users", token) or []

    if user.get("role") == "admin":
        return render_template("dashboard_admin.html",
            user=user, users=users,
            transactions=transactions,
            notifications=notifications,
            reports=reports
        )

    user_tx = [t for t in transactions if t.get("user_id") == user.get("id")]

    return render_template("dashboard_user.html",
        user=user, transactions=user_tx,
        notifications=notifications,
        reports=reports
    )

# ------------------------------------------------------
# USER CRUD (Admin)
# ------------------------------------------------------
@app.route("/users", methods=["POST"])
@login_required
def add_user():
    token = session["access_token"]
    data = request.get_json()

    resp, status = api_post("/users", data, token)
    if status in (200, 201):
        return jsonify({"ok": True, "message": "User added"}), 201

    return jsonify({"ok": False, "error": resp.get("error")}), status

@app.route("/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    token = session["access_token"]
    user = session["user"]

    if user.get("role") != "admin" and user.get("id") != user_id:
        return jsonify({"ok": False, "error": "Permission denied"}), 403

    data = request.get_json()
    url = f"{API_GATEWAY}/users/{user_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        res = requests.put(url, json=data, headers=headers, timeout=REQUEST_TIMEOUT)
        resp = _safe_json(res)

        if res.status_code in (200, 201):
            return jsonify({"ok": True, "message": "User updated", "user": resp.get("user")}), 200

        return jsonify({"ok": False, "error": resp.get("error")}), res.status_code

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    token = session["access_token"]
    user = session["user"]

    if user.get("role") != "admin":
        return jsonify({"ok": False, "error": "Admin only"}), 403

    resp, status = api_delete(f"/users/{user_id}", token)

    if status == 200:
        return jsonify({"ok": True, "message": "User deleted"}), 200

    return jsonify({"ok": False, "error": resp.get("error")}), status

# ------------------------------------------------------
# TRANSACTIONS
# ------------------------------------------------------
@app.route("/transactions", methods=["POST"])
@login_required
def create_transaction():
    token = session["access_token"]
    user = session["user"]

    data = request.get_json()
    user_id = data.get("user_id") or user["id"]

    amount = float(data.get("amount", 0))
    if amount <= 0:
        return jsonify({"ok": False, "error": "Invalid amount"}), 400

    payload = {
        "user_id": user_id,
        "type": data.get("type"),
        "amount": amount
    }

    resp, status = api_post("/transactions", payload, token)

    if status in (200, 201):
        updated = api_get(f"/users/{user_id}", token)
        if updated and "balance" in updated:
            session["user"]["balance"] = updated["balance"]

        return jsonify({"ok": True,
                        "message": "Transaction successful",
                        "balance": updated.get("balance")}), 200

    return jsonify({"ok": False, "error": resp.get("error")}), status

# ------------------------------------------------------
# TOPUP
# ------------------------------------------------------
@app.route("/topup", methods=["POST"])
@login_required
def topup_balance():
    token = session["access_token"]
    user = session["user"]

    data = request.get_json()
    amount = float(data.get("amount", 0))

    if amount <= 0:
        return jsonify({"ok": False, "error": "Invalid amount"}), 400

    resp, status = api_post(f"/users/{user['id']}/topup", {"amount": amount}, token)

    if status in (200, 201):
        updated = api_get(f"/users/{user['id']}", token)
        session["user"]["balance"] = updated.get("balance")
        return jsonify({"ok": True, "message": "Top-up successful",
                        "balance": updated.get("balance")}), 200

    return jsonify({"ok": False, "error": resp.get("error")}), status

# ------------------------------------------------------
# REPORT REQUEST
# ------------------------------------------------------
@app.route("/request-report", methods=["POST"])
@login_required
def request_report():
    token = session["access_token"]
    user = session["user"]

    resp, status = api_post("/reports", {"user_id": user["id"]}, token)

    if status in (200, 201):
        return jsonify({"ok": True, "message": "Report created"}), 200

    return jsonify({"ok": False, "error": resp.get("error")}), status

# ------------------------------------------------------
# NOTIFICATIONS
# ------------------------------------------------------
@app.route("/notifications", methods=["POST"])
@login_required
def create_notification():
    token = session["access_token"]
    user = session["user"]

    if user.get("role") != "admin":
        return jsonify({"ok": False, "error": "Admin only"}), 403

    data = request.get_json()

    if not data.get("user_id") or not data.get("message"):
        return jsonify({"ok": False, "error": "user_id and message required"}), 400

    resp, status = api_post("/notifications", data, token)

    if status in (200, 201):
        return jsonify({"ok": True, "message": "Notification sent"}), 201

    return jsonify({"ok": False, "error": resp.get("error")}), status

@app.route("/notifications", methods=["GET"])
@login_required
def get_notifications():
    token = session["access_token"]
    return jsonify(api_get("/notifications", token)), 200

# ------------------------------------------------------
# SYNC REPORTS
# ------------------------------------------------------
@app.route("/sync/all", methods=["POST"])
@login_required
def sync_all():
    token = session["access_token"]
    user = session["user"]

    if user.get("role") != "admin":
        return jsonify({"error": "Admin only"}), 403

    resp, status = api_post("/sync/all", token=token)

    return jsonify(resp), status

# ------------------------------------------------------
# Error Handlers
# ------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("error.html", message="Internal server error"), 500

# ------------------------------------------------------
# RUN SERVER
# ------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0",
            port=int(os.getenv("PORT", 8080)),
            debug=True)