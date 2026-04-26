from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import bcrypt
import os

MONGO_URI = "mongodb+srv://npatilpriyada_db_user:Mhtcet_596@cluster0.mluesum.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db     = client["hersafe"]
users  = db["users"]
history= db["history"]

auth = Blueprint("auth", __name__)

@auth.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    name      = data.get("name", "").strip()
    email     = data.get("email", "").strip().lower()
    password  = data.get("password", "")
    phone     = data.get("phone", "").strip()
    emergency = data.get("emergency_contact", "").strip()
    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if users.find_one({"email": email}):
        return jsonify({"error": "An account with this email already exists."}), 409
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    users.insert_one({
        "name": name, "email": email, "password": hashed,
        "phone": phone, "emergency_contact": emergency,
        "created_at": datetime.utcnow()
    })
    return jsonify({"message": "Account created successfully!"}), 201

@auth.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "No account found with this email."}), 404
    if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return jsonify({"error": "Incorrect password."}), 401
    return jsonify({"message": "Login successful!", "user": {
        "name": user["name"], "email": user["email"],
        "phone": user.get("phone", ""),
        "emergency_contact": user.get("emergency_contact", "")
    }}), 200

@auth.route("/history", methods=["POST"])
def save_history():
    data     = request.get_json()
    email    = data.get("email", "").strip().lower()
    text     = data.get("text", "")
    category = data.get("category", "")
    score    = data.get("score", 0)
    if not email or not text:
        return jsonify({"error": "Email and text are required."}), 400
    history.insert_one({
        "email": email, "text": text, "category": category,
        "score": score, "date": datetime.utcnow().strftime("%d/%m/%Y")
    })
    return jsonify({"message": "History saved."}), 201

@auth.route("/history", methods=["GET"])
def get_history():
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required."}), 400
    records = list(history.find({"email": email}, {"_id": 0}).sort("_id", -1).limit(50))
    return jsonify({"history": records}), 200