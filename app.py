"""
QR-Secure : QR Code Security Analyzer
-------------------------------------
A beginner-friendly cyber security mini project.
Flow: upload image -> decode QR -> analyze text/URL as a STRING -> score -> save history.

SAFETY RULE: this program NEVER opens, downloads or executes the decoded URL.
The URL is only treated as text and checked with simple rules.
"""

import os
import re
import ipaddress
import sqlite3
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, url_for

# ---- Optional libraries: show friendly message if they are missing ----
try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    from pyzbar.pyzbar import decode as zbar_decode
except Exception:  # ImportError, or missing zbar DLL on Windows
    zbar_decode = None

# ---------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # max upload = 5 MB

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# ---------------------------------------------------------------------
# Rule data (edit these lists to tune the analyzer)
# ---------------------------------------------------------------------
SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly", "buff.ly",
    "cutt.ly", "rebrand.ly", "shorturl.at", "tiny.cc", "rb.gy", "bl.ink",
    "lnkd.in", "s.id", "v.gd",
}
SUSPICIOUS_KEYWORDS = [
    "login", "signin", "verify", "update", "secure", "account", "bank",
    "password", "confirm", "wallet", "free", "gift", "prize", "winner",
    "lottery", "urgent", "suspend", "otp", "kyc", "claim", "reward",
    "billing", "payment",
]
SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "xyz", "top", "click", "zip", "work", "loan"}
BRANDS = [
    "paypal", "google", "facebook", "instagram", "amazon", "microsoft",
    "apple", "netflix", "whatsapp", "sbi", "hdfc", "icici", "paytm", "phonepe",
]
DANGEROUS_SCHEMES = ("javascript", "data", "vbscript", "file")


# =====================================================================
# 1. QR DECODING
# =====================================================================
def decode_qr(image_bytes):
    """Return a list of text values found in the QR image(s).
    Raises ValueError (friendly message) or RuntimeError (missing library)."""
    if cv2 is None or np is None:
        raise RuntimeError("OpenCV/NumPy is not installed. Run: pip install -r requirements.txt")

    data = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("The uploaded file is not a valid image.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    found = []

    # Method 1: pyzbar (usually the most reliable)
    if zbar_decode is not None:
        for attempt in (gray, cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)):
            for obj in zbar_decode(attempt):
                if obj.type == "QRCODE":
                    found.append(obj.data.decode("utf-8", errors="replace"))
            if found:
                break

    # Method 2: OpenCV's built-in detector (backup)
    if not found:
        detector = cv2.QRCodeDetector()
        try:
            ok, texts, _, _ = detector.detectAndDecodeMulti(image)
            if ok:
                found = [t for t in texts if t]
        except cv2.error:
            pass
        if not found:
            text, _, _ = detector.detectAndDecode(image)
            if text:
                found = [text]

    if not found:
        raise ValueError("No QR code was detected. Try a clearer, well-lit, uncropped image.")

    # Remove duplicates but keep order
    unique = list(dict.fromkeys(found))
    if all(item.strip() == "" for item in unique):
        raise ValueError("A QR code was detected but it is empty.")
    return [item for item in unique if item.strip()]


# =====================================================================
# 2. URL EXTRACTION
# =====================================================================
def extract_url(text):
    """Return a URL string if the QR text looks like a link, otherwise None.
    (We only build a string here. We NEVER visit it.)"""
    t = text.strip()
    low = t.lower()
    if re.match(r"^(https?|ftp)://", low):
        return t
    if re.match(r"^(" + "|".join(DANGEROUS_SCHEMES) + r"):", low):
        return t
    if " " not in t and re.match(r"^([a-z0-9-]+\.)+[a-z]{2,}(:\d+)?(/\S*)?$", low):
        return "http://" + t  # no scheme given, so HTTPS is missing
    return None


def get_registered_domain(host):
    """Simple guess of 'main domain': example.com or example.co.in"""
    labels = host.split(".")
    if len(labels) >= 3 and labels[-2] in ("co", "com", "org", "net", "gov", "ac"):
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


# =====================================================================
# 3. INDIVIDUAL CHECKS
# =====================================================================
def check_https(parsed):
    """True if the URL uses HTTPS."""
    return parsed.scheme == "https"


def is_url_shortener(host):
    """True if the host is a known URL shortener."""
    return host in SHORTENERS


def is_ip_based_url(host):
    """True if the host is an IP address (e.g. http://192.168.1.5/login)."""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def find_suspicious_keywords(text):
    """Return the list of suspicious keywords found in the text."""
    low = text.lower()
    return [word for word in SUSPICIOUS_KEYWORDS if word in low]


def analyze_domain(parsed, url):
    """Look at the domain structure. Returns a list of (message, points)."""
    host = parsed.hostname or ""
    findings = []
    labels = host.split(".")
    registered = get_registered_domain(host)

    subdomains = len(labels) - len(registered.split("."))
    if subdomains >= 3:
        findings.append((f"Too many subdomains ({subdomains}) - common in phishing", 10))

    if host.count("-") >= 2:
        findings.append(("Many hyphens in domain name", 10))

    if "@" in url:
        findings.append(("'@' symbol in URL can hide the real destination", 15))

    if "xn--" in host:
        findings.append(("Punycode domain (possible look-alike characters)", 15))

    if labels[-1] in SUSPICIOUS_TLDS:
        findings.append((f"Domain ends with a risky extension (.{labels[-1]})", 10))

    for brand in BRANDS:
        if brand in host and registered.split(".")[0] != brand:
            findings.append((f"Uses the brand name '{brand}' but is not the official domain", 25))
            break

    if len(url) > 100:
        findings.append(("Very long URL", 10))

    special = sum(url.count(c) for c in "@%-_=&~#$!*")
    if special > 10:
        findings.append((f"Excessive special characters ({special})", 10))

    try:
        if parsed.port not in (None, 80, 443):
            findings.append((f"Unusual port number ({parsed.port})", 10))
    except ValueError:
        findings.append(("Invalid port number in URL", 10))

    return findings


# =====================================================================
# 4. RISK SCORE + CLASSIFICATION
# =====================================================================
def calculate_risk_score(indicators):
    """Add up the points of all indicators (max 100)."""
    return min(100, sum(points for _, points in indicators))


def classify(score):
    """0-20 SAFE, 21-50 SUSPICIOUS, 51+ DANGEROUS"""
    if score <= 20:
        return "SAFE", "safe", "🟢"
    if score <= 50:
        return "SUSPICIOUS", "suspicious", "🟡"
    return "DANGEROUS", "dangerous", "🔴"


def get_recommendations(result):
    if result == "SAFE":
        return [
            "No major warning signs were found, but this is only a heuristic check.",
            "Still confirm the QR code came from a trusted source.",
            "Check the address bar carefully after opening any link.",
        ]
    if result == "SUSPICIOUS":
        return [
            "Do not open this link until it has been verified.",
            "Ask the person or company that provided the QR code.",
            "Never enter passwords, OTPs or card details on the linked page.",
        ]
    return [
        "Do not open this link until it has been verified.",
        "Do not scan or share this QR code further.",
        "Never enter passwords, OTPs or payment details.",
        "Report it to the organisation or to cybercrime.gov.in.",
    ]


# =====================================================================
# 5. MAIN ANALYSIS FUNCTION
# =====================================================================
def analyze_qr_content(text):
    """Analyze one decoded QR text and return a dictionary for the templates."""
    indicators = []  # list of (message, points)
    url = extract_url(text)
    report = {
        "content": text, "is_url": url is not None, "url": None, "domain": None,
        "https": None, "shortener": None, "ip_based": None,
    }

    if url is None:
        # Plain text / other data (WiFi, phone number, etc.). No link to check.
        report["type"] = "Plain text / other data (not a URL)"
        words = find_suspicious_keywords(text)
        if words:
            indicators.append((f"Suspicious keywords in text: {', '.join(words[:3])}", min(10 * len(words), 30)))
    else:
        report["type"] = "URL"
        report["url"] = url
        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
        except ValueError:
            parsed, host = None, ""
            indicators.append(("URL is malformed", 30))

        if parsed is not None:
            report["domain"] = host or "(none)"

            if parsed.scheme in DANGEROUS_SCHEMES:
                indicators.append((f"Dangerous scheme '{parsed.scheme}:' can run code or read files", 60))
            else:
                report["https"] = check_https(parsed)
                if not report["https"]:
                    indicators.append(("Connection is not encrypted (HTTPS missing)", 20))

                report["shortener"] = is_url_shortener(host)
                if report["shortener"]:
                    indicators.append(("URL shortener hides the real destination", 20))

                report["ip_based"] = is_ip_based_url(host)
                if report["ip_based"]:
                    indicators.append(("IP address used instead of a domain name", 30))
                elif host:
                    indicators.extend(analyze_domain(parsed, url))

                words = find_suspicious_keywords(url)
                if words:
                    indicators.append((f"Suspicious keywords: {', '.join(words)}", min(10 * len(words), 30)))

    score = calculate_risk_score(indicators)
    result, css, emoji = classify(score)
    report.update({
        "indicators": indicators, "score": score, "result": result,
        "css": css, "emoji": emoji, "recommendations": get_recommendations(result),
    })
    return report


# =====================================================================
# 6. DATABASE (SQLite)
# =====================================================================
def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_time TEXT NOT NULL,
                qr_content TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                result TEXT NOT NULL
            )"""
        )


def save_history(report):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO history (date_time, qr_content, risk_score, result) VALUES (?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), report["content"][:500],
             report["score"], report["result"]),
        )


def get_history():
    with get_db() as conn:
        return conn.execute(
            "SELECT id, date_time, qr_content, risk_score, result FROM history ORDER BY id DESC"
        ).fetchall()


def get_stats():
    stats = {"total": 0, "SAFE": 0, "SUSPICIOUS": 0, "DANGEROUS": 0}
    with get_db() as conn:
        for result, count in conn.execute("SELECT result, COUNT(*) FROM history GROUP BY result"):
            stats[result] = count
            stats["total"] += count
    return stats


# =====================================================================
# 7. ROUTES
# =====================================================================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def show_error(message):
    return render_template("index.html", error=message), 400


@app.route("/")
def index():
    return render_template("index.html", error=None)


@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("qr_image")
    if file is None or file.filename == "":
        return show_error("Please choose a QR code image first.")
    if not allowed_file(file.filename):
        return show_error("Unsupported file type. Please upload a PNG, JPG or JPEG image.")

    try:
        contents = decode_qr(file.read())  # file is read in memory, never saved to disk
    except ValueError as err:
        return show_error(str(err))
    except RuntimeError as err:
        return show_error(str(err))
    except Exception:
        return show_error("Something went wrong while reading the image. Please try another file.")

    results = [analyze_qr_content(text) for text in contents]

    db_warning = None
    try:
        for report in results:
            save_history(report)
    except sqlite3.Error:
        db_warning = "Analysis worked, but the result could not be saved to history."

    return render_template("result.html", results=results, db_warning=db_warning)


@app.route("/history")
def history():
    try:
        rows, stats, db_error = get_history(), get_stats(), None
    except sqlite3.Error:
        rows, stats = [], {"total": 0, "SAFE": 0, "SUSPICIOUS": 0, "DANGEROUS": 0}
        db_error = "Could not read the database."
    return render_template("history.html", rows=rows, stats=stats, db_error=db_error)


@app.route("/clear-history", methods=["POST"])
def clear_history():
    try:
        with get_db() as conn:
            conn.execute("DELETE FROM history")
    except sqlite3.Error:
        pass
    return redirect(url_for("history"))


@app.errorhandler(413)
def too_large(_):
    return show_error("File is too large. Maximum size is 5 MB.")


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
