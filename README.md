# QR-Secure: QR Code Security Analyzer

A beginner-friendly cyber security mini project. Upload or scan a QR code, decode it, analyze the text/URL
(without ever opening it) and get a **Safe / Suspicious / Dangerous** verdict with a risk score.

**Stack:** HTML/CSS/JS, Python Flask, OpenCV + pyzbar, SQLite. No paid APIs. Works locally on Windows, Python 3.11.

## Folder layout (save each file exactly here)
```
QR-Secure/
├── app.py
├── requirements.txt
├── database.db          (created automatically on first run)
├── templates/  index.html  result.html  history.html
├── static/     style.css  script.js
└── README.md
```

## Windows installation (Command Prompt or PowerShell)
```
cd C:\Users\YourName\Desktop
mkdir QR-Secure
cd QR-Secure
py -3.11 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```
PowerShell blocks activation? Run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use Command Prompt.

Then open **http://127.0.0.1:5000** in your browser. Stop the server with `Ctrl + C`.

### If pyzbar fails on Windows
pyzbar needs the *Visual C++ Redistributable Packages for Visual Studio 2013 (x64)* from Microsoft.
Even without it, the app still decodes most QR codes using OpenCV's built-in detector.

## How the risk score works (heuristic)
| Check | Points |
|---|---|
| HTTPS missing | +20 |
| URL shortener | +20 |
| IP address instead of domain | +30 |
| Suspicious keywords | +10 each (max 30) |
| Brand name in fake domain | +25 |
| Many subdomains / hyphens / risky TLD / long URL / '@' / punycode / odd port / many special chars | +10 to +15 each |
| javascript:, data:, file: scheme | +60 |

**0-20 SAFE, 21-50 SUSPICIOUS, 51+ DANGEROUS.** This is a heuristic score, **not a guarantee** that a site is safe.

## Security design
- The decoded URL is treated only as a string. It is never opened, requested, downloaded or executed.
- Uploaded images are decoded in memory and are not saved to disk (5 MB limit, PNG/JPG/JPEG only).
- Jinja2 auto-escapes QR text, so malicious QR text cannot inject HTML/JavaScript into the pages.

## Testing quickly
Make test QR codes with any free online QR generator, for example:
`https://www.google.com` (Safe), `http://bit.ly/abc123` (Suspicious), `http://192.168.1.5/login` (Dangerous).
