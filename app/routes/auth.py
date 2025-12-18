from flask import Blueprint, request, render_template, jsonify
from flask_login import login_user, logout_user
from app.models.user import User
from app.extensions import db
from app.utils.security import hash_password, verify_password


auth_bp = Blueprint("auth", __name__)

# Pagini HTML
@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validare date
    if not data or "email" not in data or "password" not in data or "full_name" not in data:
        return jsonify({"error": "INVALID_DATA", "message": "Lipsesc campuri obligatorii."}), 400

    email = data["email"].strip().lower()
    password = data["password"]
    full_name = data["full_name"].strip()
    role = data.get("role", "student")

    if "upb" not in email:
        return jsonify({
            "error": "INVALID_EMAIL",
            "message": "Email-ul trebuie să conțină domeniul @upb."
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "WEAK_PASSWORD",
            "message": "Parola trebuie să aibă cel puțin 8 caractere."
        }), 400

    if not any(c.isupper() for c in password):
        return jsonify({
            "error": "WEAK_PASSWORD",
            "message": "Parola trebuie să conțină cel puțin o literă mare."
        }), 400

    if not any(c.islower() for c in password):
        return jsonify({
            "error": "WEAK_PASSWORD",
            "message": "Parola trebuie să conțină cel puțin o literă mică."
        }), 400

    if not any(c.isdigit() for c in password):
        return jsonify({
            "error": "WEAK_PASSWORD",
            "message": "Parola trebuie să conțină cel puțin o cifră."
        }), 400

    # Email deja folosit
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "EMAIL_TAKEN", "message": "Adresa de email este deja folosită."}), 409

    # Creare utilizator
    user = User(
        email=email,
        full_name=full_name,
        role=role,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
    }), 201



@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "INVALID_DATA", "message": "Email si parola necesare."}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    user = User.query.filter_by(email=email).first()

    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "INVALID_CREDENTIALS", "message": "Email sau parola incorecte."}), 401

    login_user(user)

    return jsonify({
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout utilizatorul si redirectionează la home"""
    logout_user()
    return jsonify({"message": "Logout reusit"}), 200
