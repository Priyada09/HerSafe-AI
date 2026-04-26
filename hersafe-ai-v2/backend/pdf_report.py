"""
pdf_report.py — HerSafe AI Evidence Report Generator
Generates a professional, court-ready PDF evidence package using ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF

# ── Color palette ──────────────────────────────────────────────────────────────
PINK       = colors.HexColor("#D4537E")
PINK_LIGHT = colors.HexColor("#FBEAF0")
PINK_MID   = colors.HexColor("#F4C0D1")
DARK       = colors.HexColor("#1a1a1a")
MUTED      = colors.HexColor("#888888")
BORDER     = colors.HexColor("#E8E5DF")
SAFE_BG    = colors.HexColor("#EAF3DE")
SAFE_TEXT  = colors.HexColor("#3B6D11")
WARN_BG    = colors.HexColor("#FAEEDA")
WARN_TEXT  = colors.HexColor("#854F0B")
DANGER_BG  = colors.HexColor("#FCEBEB")
DANGER_TEXT= colors.HexColor("#A32D2D")
WHITE      = colors.white

CATEGORY_COLORS = {
    "Safe":       (SAFE_BG,   SAFE_TEXT,   colors.HexColor("#639922")),
    "Suspicious": (WARN_BG,   WARN_TEXT,   colors.HexColor("#BA7517")),
    "Dangerous":  (DANGER_BG, DANGER_TEXT, colors.HexColor("#E24B4A")),
}


def build_styles():
    base = getSampleStyleSheet()
    return {
        "report_id": ParagraphStyle("report_id", fontName="Helvetica",
            fontSize=8, textColor=MUTED, alignment=TA_RIGHT),
        "doc_title": ParagraphStyle("doc_title", fontName="Helvetica-Bold",
            fontSize=20, textColor=DARK, spaceAfter=2),
        "doc_sub": ParagraphStyle("doc_sub", fontName="Helvetica",
            fontSize=10, textColor=MUTED, spaceAfter=0),
        "section_heading": ParagraphStyle("section_heading", fontName="Helvetica-Bold",
            fontSize=9, textColor=PINK, spaceBefore=14, spaceAfter=6,
            borderPadding=(0,0,3,0)),
        "body": ParagraphStyle("body", fontName="Helvetica",
            fontSize=10, textColor=DARK, leading=15),
        "body_muted": ParagraphStyle("body_muted", fontName="Helvetica",
            fontSize=9, textColor=MUTED, leading=13),
        "message_text": ParagraphStyle("message_text", fontName="Helvetica",
            fontSize=11, textColor=DARK, leading=17,
            backColor=colors.HexColor("#FAF9F7"),
            borderPadding=10),
        "footer": ParagraphStyle("footer", fontName="Helvetica",
            fontSize=8, textColor=MUTED, alignment=TA_CENTER),
        "disclaimer": ParagraphStyle("disclaimer", fontName="Helvetica-Oblique",
            fontSize=8, textColor=MUTED, leading=12),
        "flag_label": ParagraphStyle("flag_label", fontName="Helvetica-Bold",
            fontSize=9, textColor=DARK),
    }


def severity_bar_drawing(score: int, bar_color: colors.Color) -> Drawing:
    """Draw a horizontal severity bar."""
    w, h = 160*mm, 8
    d = Drawing(w, h + 4)
    # Background track
    d.add(Rect(0, 2, w, h, rx=4, ry=4,
               fillColor=colors.HexColor("#F0EDE8"), strokeColor=None))
    # Fill
    fill_w = max(8, (score / 100) * w)
    d.add(Rect(0, 2, fill_w, h, rx=4, ry=4,
               fillColor=bar_color, strokeColor=None))
    return d


def generate_pdf_report(
    message_text: str,
    analysis_result: dict,
    sender_info: str = "Unknown",
    platform: str = "Not specified",
    victim_name: str = "Complainant",
    report_id: str = None,
) -> bytes:
    """
    Generate a PDF evidence report and return it as bytes.

    Parameters
    ----------
    message_text    : The original message being analyzed
    analysis_result : Dict from analyzer.analyze_text()
    sender_info     : Sender username / profile link
    platform        : Platform (e.g. Instagram, WhatsApp)
    victim_name     : Name of the person filing the report
    report_id       : Optional report ID (auto-generated if not provided)

    Returns
    -------
    bytes — raw PDF data, ready to write to file or send as HTTP response
    """
    if not report_id:
        report_id = f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    now = datetime.now()
    timestamp = now.strftime("%d %B %Y, %I:%M %p")
    styles = build_styles()

    category   = analysis_result.get("category", "Safe")
    score      = analysis_result.get("severity_score", 0)
    alert      = analysis_result.get("alert", "")
    flags      = analysis_result.get("flags", [])
    sentiment  = analysis_result.get("sentiment", None)

    bg_color, text_color, bar_color = CATEGORY_COLORS.get(
        category, (SAFE_BG, SAFE_TEXT, colors.HexColor("#639922")))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm,
        title=f"HerSafe AI Evidence Report – {report_id}",
        author="HerSafe AI",
    )

    story = []

    # ── Header bar (pink accent row) ───────────────────────────────────────────
    header_table = Table(
        [[
            Paragraph("HerSafe AI", ParagraphStyle("hdr", fontName="Helvetica-Bold",
                fontSize=13, textColor=WHITE)),
            Paragraph(f"Report ID: {report_id}", ParagraphStyle("hdr_r",
                fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#F4C0D1"),
                alignment=TA_RIGHT)),
        ]],
        colWidths=["60%", "40%"],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PINK),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("ROUNDEDCORNERS", (0,0), (-1,-1), [6,6,0,0]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # ── Document title ─────────────────────────────────────────────────────────
    story.append(Paragraph("Evidence Report", styles["doc_title"]))
    story.append(Paragraph(
        "AI-Powered Online Threat Detection — HerSafe AI", styles["doc_sub"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=BORDER, spaceAfter=10))

    # ── Meta table ─────────────────────────────────────────────────────────────
    story.append(Paragraph("REPORT DETAILS", styles["section_heading"]))
    meta_data = [
        ["Report ID",        report_id],
        ["Generated on",     timestamp],
        ["Complainant",      victim_name],
        ["Sender / Account", sender_info],
        ["Platform",         platform],
    ]
    meta_table = Table(meta_data, colWidths=[45*mm, None])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), MUTED),
        ("TEXTCOLOR", (1,0), (1,-1), DARK),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("LINEBELOW", (0,-1), (-1,-1), 0.5, BORDER),
    ]))
    story.append(meta_table)

    # ── Original message ───────────────────────────────────────────────────────
    story.append(Paragraph("ORIGINAL MESSAGE", styles["section_heading"]))
    msg_table = Table(
        [[Paragraph(message_text or "(no message provided)",
                    styles["message_text"])]],
        colWidths=["100%"],
    )
    msg_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#FAF9F7")),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("ROUNDEDCORNERS",(0,0), (-1,-1), [6,6,6,6]),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("RIGHTPADDING",  (0,0), (-1,-1), 12),
    ]))
    story.append(msg_table)

    # ── Verdict banner ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(Paragraph("THREAT ASSESSMENT", styles["section_heading"]))

    verdict_table = Table(
        [[
            Paragraph(f"<b>{category}</b>",
                ParagraphStyle("verd", fontName="Helvetica-Bold",
                    fontSize=15, textColor=text_color)),
            Paragraph(f"Severity Score: <b>{score}%</b>",
                ParagraphStyle("verd_score", fontName="Helvetica",
                    fontSize=10, textColor=text_color, alignment=TA_RIGHT)),
        ]],
        colWidths=["50%", "50%"],
    )
    verdict_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg_color),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("ROUNDEDCORNERS",(0,0), (-1,-1), [6,6,0,0]),
    ]))
    story.append(verdict_table)

    # Severity bar
    bar_row = Table(
        [[severity_bar_drawing(score, bar_color)]],
        colWidths=["100%"],
    )
    bar_row.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg_color),
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("ROUNDEDCORNERS",(0,0), (-1,-1), [0,0,6,6]),
    ]))
    story.append(bar_row)
    story.append(Spacer(1, 8))

    # Alert message
    alert_table = Table(
        [[Paragraph(alert, ParagraphStyle("alrt", fontName="Helvetica",
            fontSize=10, textColor=text_color, leading=15))]],
        colWidths=["100%"],
    )
    alert_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg_color),
        ("BOX",           (0,0), (-1,-1), 0.5, bar_color),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("RIGHTPADDING",  (0,0), (-1,-1), 12),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("ROUNDEDCORNERS",(0,0), (-1,-1), [4,4,4,4]),
    ]))
    story.append(alert_table)

    # ── Detected flags ─────────────────────────────────────────────────────────
    if flags:
        story.append(Paragraph("DETECTED PATTERNS", styles["section_heading"]))
        flag_rows = [[Paragraph(f"• {f}", styles["body"])] for f in flags]
        flag_table = Table(flag_rows, colWidths=["100%"])
        flag_table.setStyle(TableStyle([
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ]))
        story.append(flag_table)

    # ── Sentiment ──────────────────────────────────────────────────────────────
    if sentiment is not None:
        story.append(Paragraph("SENTIMENT ANALYSIS", styles["section_heading"]))
        label = "Positive" if sentiment > 0.2 else "Negative" if sentiment < -0.2 else "Neutral"
        story.append(Paragraph(
            f"Polarity score: <b>{sentiment}</b> ({label})",
            styles["body"]))

    # ── Recommended actions ────────────────────────────────────────────────────
    story.append(Paragraph("RECOMMENDED ACTIONS", styles["section_heading"]))
    if category == "Dangerous":
        actions = [
            "Block the sender immediately on all platforms.",
            "Do not respond to or engage with the sender.",
            "Screenshot and preserve all original messages with timestamps.",
            "File a complaint with your local Cyber Crime Cell.",
            "Contact emergency services (112) if you feel in immediate danger.",
            "Report the account to the platform (Instagram, WhatsApp, etc.).",
            "Inform a trusted person (family member, friend, or counsellor).",
        ]
    elif category == "Suspicious":
        actions = [
            "Restrict or mute the sender on the platform.",
            "Monitor for further escalation.",
            "Save screenshots of suspicious messages.",
            "Inform a trusted contact about the situation.",
            "Consider reporting to the platform's trust & safety team.",
        ]
    else:
        actions = [
            "No immediate action required.",
            "Continue to monitor if you suspect a pattern.",
        ]

    for i, action in enumerate(actions, 1):
        story.append(Paragraph(f"{i}. {action}", styles["body"]))
        story.append(Spacer(1, 2))

    # ── Legal note ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=BORDER, spaceBefore=4, spaceAfter=6))
    story.append(Paragraph(
        "This report was automatically generated by HerSafe AI for informational and "
        "documentation purposes. It is not a substitute for professional legal advice. "
        "For cybercrime reporting in India, visit cybercrime.gov.in or call 1930.",
        styles["disclaimer"]
    ))

    doc.build(story)
    return buffer.getvalue()
