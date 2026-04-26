"""
forgot_password.py — HerSafe AI Forgot Password with Email OTP
Endpoints:
  POST /forgot-password  — send OTP to email
  POST /verify-otp       — verify OTP
  POST /reset-password   — reset password
"""

from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
import bcrypt
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ── MongoDB Connection ─────────────────────────────────────────────────────────
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://npatilpriyada_db_user:Mhtcet_596@cluster0.mluesum.mongodb.net/?appName=Cluster0"
)

client  = MongoClient(MONGO_URI)
db      = client["hersafe"]
users   = db["users"]
otps    = db["otps"]

# ── Email Config ───────────────────────────────────────────────────────────────
SMTP_EMAIL    = os.environ.get("HERSAFE_EMAIL", "npatilpriyada@gmail.com")
SMTP_PASSWORD = os.environ.get("HERSAFE_EMAIL_PASS", "eiayqfyupvsrsqix")

forgot = Blueprint("forgot", __name__)


def send_otp_email(to_email, otp):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🔐 HerSafe AI — Password Reset OTP"
        msg["From"]    = SMTP_EMAIL
        msg["To"]      = to_email

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:24px;background:#fff;border-radius:12px;border:1px solid #f4c0d1;">
            <div style="text-align:center;margin-bottom:24px;">
                <h2 style="color:#e8476a;margin:0;">🛡️ HerSafe AI</h2>
                <p style="color:#888;font-size:13px;">Password Reset Request</p>
            </div>
            <p style="color:#333;">Your OTP for password reset is:</p>
            <div style="text-align:center;margin:24px 0;">
                <span style="font-size:36px;font-weight:bold;letter-spacing:8px;color:#e8476a;background:#fdedf0;padding:16px 32px;border-radius:12px;">{otp}</span>
            </div>
            <p style="color:#888;font-size:13px;">This OTP is valid for <strong>10 minutes</strong>. Do not share it with anyone.</p>
            <p style="color:#888;font-size:12px;">If you did not request this, please ignore this email.</p>
            <hr style="border:none;border-top:1px solid #f0ede8;margin:20px 0;"/>
            <p style="color:#bbb;font-size:11px;text-align:center;">HerSafe AI — Protecting Women. Empowering Safety.</p>
        </div>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# ── Send OTP ───────────────────────────────────────────────────────────────────
@forgot.route("/forgot-password", methods=["POST"])
def forgot_password():
    data  = request.get_json()
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required."}), 400

    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "No account found with this email."}), 404

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # Save OTP to database (expires in 10 minutes)
    otps.delete_many({"email": email})  # remove old OTPs
    otps.insert_one({
        "email":      email,
        "otp":        otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "verified":   False
    })

    # Send email
    sent = send_otp_email(email, otp)
    if not sent:
        return jsonify({"error": "Failed to send OTP. Please try again."}), 500

    return jsonify({"message": f"OTP sent to {email}"}), 200


# ── Verify OTP ─────────────────────────────────────────────────────────────────
@forgot.route("/verify-otp", methods=["POST"])
def verify_otp():
    data  = request.get_json()
    email = data.get("email", "").strip().lower()
    otp   = data.get("otp", "").strip()

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required."}), 400

    record = otps.find_one({"email": email, "otp": otp})

    if not record:
        return jsonify({"error": "Invalid OTP. Please try again."}), 400

    if datetime.utcnow() > record["expires_at"]:
        return jsonify({"error": "OTP has expired. Please request a new one."}), 400

    # Mark OTP as verified
    otps.update_one({"email": email, "otp": otp}, {"$set": {"verified": True}})

    return jsonify({"message": "OTP verified successfully!"}), 200


# ── Reset Password ─────────────────────────────────────────────────────────────
@forgot.route("/reset-password", methods=["POST"])
def reset_password():
    data         = request.get_json()
    email        = data.get("email", "").strip().lower()
    otp          = data.get("otp", "").strip()
    new_password = data.get("new_password", "")

    if not email or not otp or not new_password:
        return jsonify({"error": "All fields are required."}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    # Check OTP is verified
    record = otps.find_one({"email": email, "otp": otp, "verified": True})
    if not record:
        return jsonify({"error": "OTP not verified. Please verify OTP first."}), 400

    # Hash new password
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

    # Update password
    users.update_one({"email": email}, {"$set": {"password": hashed}})

    # Delete used OTP
    otps.delete_many({"email": email})

    return jsonify({"message": "Password reset successfully! Please login."}), 200
