# HerSafe AI — AI-Powered Online Threat Detection for Women's Safety

![HerSafe AI](https://img.shields.io/badge/HerSafe-AI-D4537E?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask)
![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> Real-time AI-powered detection of threats, harassment, and abusive language targeting women online — with PDF evidence reports, trusted contact alerts, and a browser extension for Instagram, Twitter/X, and WhatsApp Web.

---

## Features

- **Threat Analysis** — Classifies messages as Safe, Suspicious, or Dangerous using a 3-layer NLP engine
- **PDF Evidence Report** — Generates a professional, court-ready evidence package (ReportLab)
- **Trusted Contact Alerts** — Sends formatted HTML email alerts with PDF attachment via Gmail SMTP
- **Browser Extension** — Real-time scanning on Instagram, Twitter/X, and WhatsApp Web with inline threat badges
- **Client-side Fallback** — Works offline with a built-in JS analysis engine if backend is unavailable

---

## Project Structure

```
hersafe-ai/
├── backend/
│   ├── app.py             ← Flask API (4 endpoints)
│   ├── analyzer.py        ← NLP threat detection engine
│   ├── pdf_report.py      ← PDF evidence report generator
│   ├── alert_system.py    ← Trusted contact email alerts
│   └── requirements.txt
├── extension/
│   ├── manifest.json      ← Chrome Manifest V3
│   ├── popup.html         ← Extension popup UI
│   ├── content.js         ← Auto-scans messages on social platforms
│   ├── content.css        ← Injected badge styles
│   └── background.js      ← Notifications + message passing
├── frontend/
│   └── index.html         ← Standalone web UI (no build step)
├── .env.example
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/hersafe-ai.git
cd hersafe-ai
```

### 2. Set up the backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download TextBlob language data (one-time)
python -m textblob.download_corpora
```

### 3. Configure email credentials (for alert feature)

```bash
cp ../.env.example .env
# Edit .env and fill in your Gmail credentials
```

Or export directly:

```bash
export HERSAFE_EMAIL="your@gmail.com"
export HERSAFE_EMAIL_PASS="your-16-char-app-password"
```

> **How to get a Gmail App Password:**
> Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
> → Select app: Mail → Select device: Other → Name it "HerSafe AI" → Copy the 16-char password

### 4. Start the Flask server

```bash
python app.py
# Server runs at http://localhost:5000
```

### 5. Open the frontend

```bash
# Just open in your browser — no build step needed
open ../frontend/index.html        # macOS
start ../frontend/index.html       # Windows
xdg-open ../frontend/index.html    # Linux
```

---

## API Reference

### `POST /analyze`
Analyze text and return threat classification.

**Request:**
```json
{ "text": "I know where you live and I will find you." }
```

**Response:**
```json
{
  "category": "Dangerous",
  "severity_score": 75,
  "alert": "⛔ Serious threat indicators detected...",
  "flags": ["Threatening language", "Harassment pattern"],
  "sentiment": -0.7
}
```

---

### `POST /report`
Analyze text and return a PDF evidence report as a file download.

**Request:**
```json
{
  "text": "threatening message...",
  "victim_name": "Priya",
  "sender_info": "@suspicious_user",
  "platform": "Instagram"
}
```

**Response:** PDF file download

---

### `POST /alert`
Analyze text and send an email alert to a trusted contact.

**Request:**
```json
{
  "text": "threatening message...",
  "trusted_email": "trusted@example.com",
  "victim_name": "Priya"
}
```

**Response:**
```json
{
  "analysis": { ... },
  "alert_sent": true,
  "message": "Alert sent to trusted@example.com",
  "report_id": "HS-20260425-AB12"
}
```

---

### `POST /full`
All-in-one: analyze + generate PDF + send alert email with PDF attached.

**Request:**
```json
{
  "text": "threatening message...",
  "victim_name": "Priya",
  "sender_info": "@suspicious_user",
  "platform": "Instagram",
  "trusted_email": "trusted@example.com"
}
```

---

## How the Detection Engine Works

The analyzer runs three layers in sequence — no model training required:

| Layer | What it checks | Score weight |
|-------|---------------|-------------|
| Keyword lexicons | Threats, abuse, harassment, manipulation | 12–30 pts per hit |
| Tone signals | Excessive caps, repeated exclamation marks | 5–10 pts |
| Sentiment analysis | TextBlob polarity (−1.0 to +1.0) | 8–15 pts |

**Score thresholds:**

| Score | Category | Color |
|-------|----------|-------|
| 0–19  | Safe | 🟢 Green |
| 20–59 | Suspicious | 🟡 Yellow |
| 60–100 | Dangerous | 🔴 Red |

---

## Browser Extension Setup

1. Open `chrome://extensions` in Chrome
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked**
4. Select the `/extension` folder
5. Visit Instagram, Twitter/X, or WhatsApp Web

The extension automatically scans incoming messages and injects threat badges inline. Click any badge to open the full analysis in the popup.

**Extension features:**
- Auto-scan with MutationObserver (real-time new messages)
- Desktop notifications for Dangerous verdicts
- Manual analyze tab in popup
- One-click PDF report download from popup
- One-click trusted contact alert from popup
- Per-platform toggles in Settings tab
- Scan statistics counter

---

## Upgrading to HuggingFace (Optional)

To use a real pretrained toxicity model, replace the core logic in `analyzer.py`:

```python
from transformers import pipeline

classifier = pipeline("text-classification", model="unitary/toxic-bert")

def analyze_text(text: str) -> dict:
    result = classifier(text)[0]
    score = int(result["score"] * 100)
    category = "Dangerous" if score >= 60 else "Suspicious" if score >= 20 else "Safe"
    # ... rest of return dict
```

Install additional deps:
```bash
pip install transformers torch
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JS |
| Backend | Python, Flask, Flask-CORS |
| NLP | TextBlob (sentiment), custom keyword lexicons |
| PDF | ReportLab |
| Email | Python smtplib + Gmail SMTP |
| Extension | Chrome Manifest V3, Vanilla JS |

---

## Roadmap

- [ ] Multilingual support (Hindi, Marathi, Tamil) via XLM-RoBERTa
- [ ] HuggingFace toxic-bert model integration
- [ ] Bulk CSV message analysis
- [ ] Threat history dashboard with charts
- [ ] Firefox extension support
- [ ] HuggingFace Spaces deployment (no local server needed)

---

## Resources

- Cyber Crime Reporting (India): [cybercrime.gov.in](https://cybercrime.gov.in)
- National Helpline: **1930**
- Emergency: **112**
- iCall Mental Health: **9152987821**

---

## Disclaimer

This is a prototype for educational and demonstration purposes. It is not a substitute for professional legal advice or law enforcement. In an emergency, contact local authorities immediately.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
