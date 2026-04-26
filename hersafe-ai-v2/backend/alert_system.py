"""
alert_system.py — HerSafe AI Trusted Contact Alert System

Sends email alerts to a pre-registered trusted contact when a
Dangerous threat is detected. Uses Python's built-in smtplib.

For hackathon/demo: uses Gmail SMTP with App Passwords.
For production: swap with SendGrid / AWS SES.
"""

import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime


# ── Configuration ──────────────────────────────────────────────────────────────
# Set these via environment variables in production.
# For demo, you can hardcode temporarily — but never commit real credentials.

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "465"))
SENDER_EMAIL  = os.getenv("HERSAFE_EMAIL", "")        # your Gmail address
SENDER_PASS   = os.getenv("HERSAFE_EMAIL_PASS", "")   # Gmail App Password


# ── Email templates ────────────────────────────────────────────────────────────

def build_email_html(victim_name: str, category: str, score: int,
                     message_preview: str, alert_msg: str,
                     flags: list, report_id: str) -> str:
    color_map = {
        "Safe":       ("#EAF3DE", "#3B6D11", "#639922"),
        "Suspicious": ("#FAEEDA", "#854F0B", "#BA7517"),
        "Dangerous":  ("#FCEBEB", "#A32D2D", "#E24B4A"),
    }
    bg, text, accent = color_map.get(category, color_map["Safe"])

    flags_html = "".join(
        f'<span style="display:inline-block;background:{bg};color:{text};'
        f'padding:3px 10px;border-radius:20px;font-size:12px;'
        f'margin:2px;font-weight:600">{f}</span>'
        for f in flags
    ) if flags else "<span style='color:#888'>None detected</span>"

    preview_escaped = message_preview.replace("<", "&lt;").replace(">", "&gt;")

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#FAF9F7;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:32px 16px;">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:16px;overflow:hidden;
                    border:1px solid #E8E5DF;">

        <!-- Header -->
        <tr><td style="background:#D4537E;padding:20px 28px;">
          <div style="color:#fff;font-size:18px;font-weight:700;">HerSafe AI</div>
          <div style="color:#F4C0D1;font-size:12px;margin-top:2px;">
            Safety Alert — Report {report_id}
          </div>
        </td></tr>

        <!-- Greeting -->
        <tr><td style="padding:24px 28px 0;">
          <p style="margin:0;font-size:15px;color:#1a1a1a;line-height:1.6">
            Hello,<br><br>
            <b>{victim_name}</b> has received a message that HerSafe AI has
            classified as <b style="color:{accent}">{category}</b>.
            This alert has been sent to you as their trusted contact.
          </p>
        </td></tr>

        <!-- Verdict badge -->
        <tr><td style="padding:16px 28px 0;">
          <div style="background:{bg};border-radius:10px;padding:14px 18px;
                      display:flex;align-items:center;gap:10px;">
            <span style="font-size:20px;font-weight:700;color:{text}">
              {category}
            </span>
            <span style="margin-left:auto;font-size:13px;color:{text}">
              Severity: <b>{score}%</b>
            </span>
          </div>
          <!-- severity bar -->
          <div style="background:#F0EDE8;border-radius:99px;height:8px;margin-top:6px;">
            <div style="background:{accent};width:{score}%;height:8px;
                        border-radius:99px;"></div>
          </div>
        </td></tr>

        <!-- Alert message -->
        <tr><td style="padding:12px 28px 0;">
          <div style="background:{bg};border-left:3px solid {accent};
                      border-radius:0 8px 8px 0;padding:12px 14px;
                      font-size:13px;color:{text};line-height:1.6">
            {alert_msg}
          </div>
        </td></tr>

        <!-- Original message -->
        <tr><td style="padding:20px 28px 0;">
          <div style="font-size:11px;font-weight:700;color:#aaa;
                      letter-spacing:0.05em;text-transform:uppercase;
                      margin-bottom:8px">Flagged message</div>
          <div style="background:#FAF9F7;border:1px solid #E8E5DF;
                      border-radius:8px;padding:14px;font-size:13px;
                      color:#333;line-height:1.7;font-style:italic">
            "{preview_escaped}"
          </div>
        </td></tr>

        <!-- Detected patterns -->
        <tr><td style="padding:16px 28px 0;">
          <div style="font-size:11px;font-weight:700;color:#aaa;
                      letter-spacing:0.05em;text-transform:uppercase;
                      margin-bottom:8px">Detected patterns</div>
          <div>{flags_html}</div>
        </td></tr>

        <!-- Actions -->
        <tr><td style="padding:20px 28px;">
          <div style="font-size:11px;font-weight:700;color:#aaa;
                      letter-spacing:0.05em;text-transform:uppercase;
                      margin-bottom:10px">What you can do</div>
          <ul style="margin:0;padding:0 0 0 18px;color:#333;
                     font-size:13px;line-height:2">
            <li>Check in with {victim_name} immediately</li>
            <li>Help them block and report the sender</li>
            <li>Encourage reporting to Cyber Crime Cell (cybercrime.gov.in)</li>
            <li>Emergency helpline: <b>112</b> | iCall: <b>9152987821</b></li>
          </ul>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#FAF9F7;padding:16px 28px;
                       border-top:1px solid #E8E5DF;">
          <p style="margin:0;font-size:11px;color:#aaa;text-align:center">
            Sent by HerSafe AI &nbsp;·&nbsp; {datetime.now().strftime('%d %b %Y, %I:%M %p')}<br>
            This is an automated safety alert. Please do not reply to this email.
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def send_alert_email(
    trusted_email: str,
    victim_name: str,
    analysis_result: dict,
    message_text: str,
    report_id: str,
    pdf_bytes: bytes = None,
) -> dict:
    """
    Send an alert email to the trusted contact.

    Parameters
    ----------
    trusted_email   : Recipient email address
    victim_name     : Name of the person who received the threat
    analysis_result : Dict from analyzer.analyze_text()
    message_text    : The original threatening message
    report_id       : Report ID for reference
    pdf_bytes       : Optional PDF report to attach

    Returns
    -------
    dict with { success: bool, message: str }
    """
    if not SENDER_EMAIL or not SENDER_PASS:
        return {
            "success": False,
            "message": (
                "Email credentials not configured. "
                "Set HERSAFE_EMAIL and HERSAFE_EMAIL_PASS environment variables."
            )
        }

    category = analysis_result.get("category", "Safe")
    score    = analysis_result.get("severity_score", 0)
    alert    = analysis_result.get("alert", "")
    flags    = analysis_result.get("flags", [])

    # Limit message preview to 300 chars
    preview = message_text[:300] + ("..." if len(message_text) > 300 else "")

    subject = (
        f"🚨 HerSafe AI Alert: {category} threat detected for {victim_name}"
        if category == "Dangerous"
        else f"⚠️ HerSafe AI Notice: Suspicious message flagged for {victim_name}"
    )

    html_body = build_email_html(
        victim_name=victim_name,
        category=category,
        score=score,
        message_preview=preview,
        alert_msg=alert,
        flags=flags,
        report_id=report_id,
    )

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = f"HerSafe AI <{SENDER_EMAIL}>"
    msg["To"]      = trusted_email

    # HTML body
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Attach PDF if provided
    if pdf_bytes:
        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header(
            "Content-Disposition", "attachment",
            filename=f"HerSafe-Evidence-{report_id}.pdf"
        )
        msg.attach(attachment)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, trusted_email, msg.as_string())
        return {"success": True, "message": f"Alert sent to {trusted_email}"}
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "Email authentication failed. Check your Gmail App Password."
        }
    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}


def should_send_alert(category: str) -> bool:
    """Only send alerts for Suspicious or Dangerous verdicts."""
    return category in ("Suspicious", "Dangerous")
