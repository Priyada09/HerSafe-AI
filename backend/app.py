"""
app.py — HerSafe AI Flask Backend (v2)
Endpoints:
  POST /analyze          — analyze text, return JSON result
  POST /report           — analyze + generate PDF evidence report
  POST /alert            — analyze + send trusted contact email alert
  POST /full             — analyze + generate PDF + send alert (all-in-one)
  POST /signup           — register new user (MongoDB)
  POST /login            — login user (MongoDB)
  POST /history          — save analysis history
  GET  /history          — get user analysis history
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import uuid
from datetime import datetime

from analyzer import analyze_text
from pdf_report import generate_pdf_report
from alert_system import send_alert_email, should_send_alert
from auth import auth

app = Flask(__name__)
CORS(app)

# Register auth blueprint
app.register_blueprint(auth)


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "HerSafe AI v2 running",
        "endpoints": ["/analyze", "/report", "/alert", "/full", "/signup", "/login", "/history"]
    })


# ── 1. Analyze only ────────────────────────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400
    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Text cannot be empty"}), 400
    return jsonify(analyze_text(text))


# ── 2. Generate PDF evidence report ───────────────────────────────────────────
@app.route("/report", methods=["POST"])
def report():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    text        = data.get("text", "").strip()
    sender_info = data.get("sender_info", "Unknown")
    platform    = data.get("platform", "Not specified")
    victim_name = data.get("victim_name", "Complainant")
    report_id   = f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"

    result   = analyze_text(text)
    pdf_data = generate_pdf_report(
        message_text=text,
        analysis_result=result,
        sender_info=sender_info,
        platform=platform,
        victim_name=victim_name,
        report_id=report_id,
    )

    return send_file(
        io.BytesIO(pdf_data),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"HerSafe-Evidence-{report_id}.pdf",
    )


# ── 3. Send trusted contact alert ─────────────────────────────────────────────
@app.route("/alert", methods=["POST"])
def alert():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    text          = data.get("text", "").strip()
    trusted_email = data.get("trusted_email", "")
    victim_name   = data.get("victim_name", "User")

    if not trusted_email:
        return jsonify({"error": "Missing 'trusted_email' field"}), 400

    result    = analyze_text(text)
    report_id = f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if not should_send_alert(result["category"]):
        return jsonify({
            "analysis": result,
            "alert_sent": False,
            "message": "No alert sent — message classified as Safe."
        })

    alert_result = send_alert_email(
        trusted_email=trusted_email,
        victim_name=victim_name,
        analysis_result=result,
        message_text=text,
        report_id=report_id,
    )

    return jsonify({
        "analysis":   result,
        "alert_sent": alert_result["success"],
        "message":    alert_result["message"],
        "report_id":  report_id,
    })


# ── 4. Full pipeline: analyze + PDF + alert ────────────────────────────────────
@app.route("/full", methods=["POST"])
def full_pipeline():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    text          = data.get("text", "").strip()
    sender_info   = data.get("sender_info", "Unknown")
    platform      = data.get("platform", "Not specified")
    victim_name   = data.get("victim_name", "User")
    trusted_email = data.get("trusted_email", "")
    report_id     = f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"

    result = analyze_text(text)

    pdf_data = generate_pdf_report(
        message_text=text,
        analysis_result=result,
        sender_info=sender_info,
        platform=platform,
        victim_name=victim_name,
        report_id=report_id,
    )

    alert_status = {"sent": False, "message": "No alert needed (Safe)"}
    if trusted_email and should_send_alert(result["category"]):
        email_result = send_alert_email(
            trusted_email=trusted_email,
            victim_name=victim_name,
            analysis_result=result,
            message_text=text,
            report_id=report_id,
            pdf_bytes=pdf_data,
        )
        alert_status = {
            "sent":    email_result["success"],
            "message": email_result["message"],
        }

    return jsonify({
        "analysis":    result,
        "report_id":   report_id,
        "pdf_ready":   True,
        "pdf_endpoint": f"/report",
        "alert":       alert_status,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
