# QR-Secure: QR Code Security Analyzer - Project Report

## 1. Abstract
QR codes are used everywhere (payments, menus, posters), but attackers hide phishing links inside them ("quishing"). A human cannot read a QR code, so a fake link is easy to hide. QR-Secure is a Flask web application that decodes a QR image using OpenCV and pyzbar, analyzes the text or URL with rule-based checks (HTTPS, shorteners, IP address, keywords, domain structure), calculates a risk score, classifies the QR as Safe, Suspicious or Dangerous, warns the user and stores the history in SQLite. The link is never opened.

## 2. Problem Statement
Users scan QR codes without knowing where they lead. Malicious QR codes can lead to phishing pages, fake payment pages or malware. There is no simple, free, offline tool that lets a normal user check a QR code *before* opening it.

## 3. Objectives
- Decode QR codes from uploaded images (and webcam capture).
- Analyze the decoded URL/text without visiting it.
- Give a numeric risk score and a Safe/Suspicious/Dangerous result.
- Warn users and give security recommendations.
- Store history and show a simple dashboard.

## 4. Existing System
Phone camera apps open or preview links directly. Online scanners often need internet, may upload your data, or use paid APIs (e.g. VirusTotal limits, Google Safe Browsing keys). Most give no explanation of *why* a link is risky.

## 5. Proposed System
A local web app that decodes the QR, applies transparent rules, shows the reasons behind each score point, and keeps a history. It uses no paid APIs and does not connect to the scanned website.

## 6. Advantages
Free; runs offline; safe (never opens the link); explains results; simple code; easy to extend (add rules or ML); private (images are not stored).

## 7. System Requirements
**Hardware:** any PC with 4 GB RAM, webcam (optional). **Software:** Windows 10/11, Python 3.11, modern browser (Chrome/Edge/Firefox), Flask, OpenCV, NumPy, pyzbar, SQLite (built into Python).

## 8. Functional Requirements
1. Upload PNG/JPG/JPEG QR images.
2. Capture QR from webcam.
3. Decode one or multiple QR codes.
4. Extract and analyze URLs; handle plain text.
5. Calculate risk score and classify.
6. Show a report and warnings.
7. Save history in SQLite; show dashboard counts.
8. Show friendly error messages.

## 9. Non-functional Requirements
- **Security:** never open/download/execute URLs; escape output; file size/type limits.
- **Usability:** simple responsive UI.
- **Performance:** result in about 1 second.
- **Reliability:** handles errors without showing Python tracebacks.
- **Portability:** runs locally on Windows.
- **Maintainability:** small separate functions.

## 10. System Architecture
```
 +-----------+   image   +--------------------------+       +-----------+
 |  Browser  | --------> |  Flask (app.py)          | <---> |  SQLite   |
 | HTML/CSS/ | <-------- |  1 decode_qr()           |       | database  |
 |    JS     |  HTML     |  2 extract_url()         |       +-----------+
 +-----------+  report   |  3 checks + risk score   |
                         |  4 classify()            |
                         +--------------------------+
                          (OpenCV + pyzbar for decoding)
```
Three layers: Presentation (templates, CSS, JS), Application logic (Flask + Python analysis), Data (SQLite).

## 11. Module Description
| Module | Purpose |
|---|---|
| QR Decoder | `decode_qr()` reads the image with OpenCV and decodes with pyzbar (OpenCV detector as backup) |
| URL Extractor | `extract_url()` decides whether the text is a link |
| Security Checks | `check_https`, `is_url_shortener`, `is_ip_based_url`, `find_suspicious_keywords`, `analyze_domain` |
| Risk Engine | `calculate_risk_score()`, `classify()` |
| Database | `init_db`, `save_history`, `get_history`, `get_stats` |
| Web UI | `index.html`, `result.html`, `history.html`, `style.css`, `script.js` |

## 12. Data Flow
Level 0: User -> [QR-Secure] -> Report.
Level 1: User uploads image -> Decoder -> text -> URL Extractor -> Security checks -> Risk score -> Classifier -> (a) Result page (b) SQLite history -> Dashboard.

## 13. Algorithm
1. Receive image; validate extension and size.
2. Decode image; if none found or empty, show an error.
3. For each decoded text: if it is a URL, parse it (string only).
4. score = 0. Add points: no HTTPS +20; shortener +20; IP host +30; keywords +10 each (max 30); domain tricks +10 to +25; dangerous scheme +60.
5. score = min(score, 100).
6. score <= 20 SAFE; <= 50 SUSPICIOUS; else DANGEROUS.
7. Save to SQLite; display the report with warning if not SAFE.

## 14. Flowchart
```
[Start] -> [Upload/Scan image] -> <Valid image?> --No--> [Error message] -> [End]
                                        |Yes
                              <QR detected & not empty?> --No--> [Error message]
                                        |Yes
                                  [Decode text]
                                        |
                                   <Is a URL?> --No--> [Check text keywords]
                                        |Yes                     |
                        [Run URL checks, add risk points] <------+
                                        |
                                [Calculate score]
                                        |
                       <0-20?> Safe  <21-50?> Suspicious  <51+> Dangerous
                                        |
                          [Save history] -> [Show report + warning] -> [End]
```

## 15. Database Design
Table **history**
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key, auto increment |
| date_time | TEXT | e.g. 2026-09-28 14:30:05 |
| qr_content | TEXT | Decoded text (max 500 chars) |
| risk_score | INTEGER | 0-100 |
| result | TEXT | SAFE / SUSPICIOUS / DANGEROUS |

## 16. Testing
Unit testing of each function, functional testing through the browser, error/negative testing (bad files), and security testing (confirm no network request is made to the QR URL, HTML in QR text is escaped).

## 17. Sample Test Cases
| # | Input | Expected |
|---|---|---|
| 1 | QR of `https://www.google.com` | Score 0, SAFE |
| 2 | QR of `http://bit.ly/abc123` | Score 40, SUSPICIOUS |
| 3 | QR of `http://192.168.1.5/login` | Score 60, DANGEROUS |
| 4 | QR of `http://paypal-secure-login.verify-account.tk/update` | Score 95, DANGEROUS |
| 5 | QR of `Hello World` | Plain text, SAFE |
| 6 | Image without QR | Error: no QR detected |
| 7 | `.pdf` or `.gif` file | Error: unsupported file type |
| 8 | Text file renamed `.png` | Error: not a valid image |
| 9 | Image with 2 QR codes | 2 separate reports |
| 10 | No file chosen | Error: choose a file |
| 11 | After tests | History and dashboard counts increase |
| 12 | QR text `<script>alert(1)</script>` | Shown as text, no popup |

## 18. Future Enhancements
Machine learning URL classifier (Random Forest on URL features, trained on a free dataset); WHOIS domain age check; offline blacklist (e.g. PhishTank download); live video scanning; user login; export PDF report; browser extension; mobile app.

## 19. Conclusion
QR-Secure shows how basic rule-based cyber security techniques can protect users from malicious QR codes without paid services. It teaches web development, image processing, URL analysis and database use. The result is a heuristic and should be combined with user awareness.

## 20. Viva Questions and Answers
1. **What is QR-Secure?** A web app that decodes QR codes and classifies them as Safe, Suspicious or Dangerous.
2. **What is quishing?** QR-code phishing: a malicious link hidden in a QR code.
3. **How is a QR code decoded?** OpenCV loads the image into a pixel array; pyzbar finds the three corner squares, reads the black/white modules and converts them to text.
4. **Why is HTTPS checked?** HTTP is not encrypted, so data can be stolen. Missing HTTPS adds risk. (HTTPS alone does not prove a site is honest.)
5. **Why are URL shorteners risky?** They hide the real destination.
6. **Why is an IP-based URL suspicious?** Real services use domain names; attackers use raw IPs to avoid registering domains.
7. **Is your score 100% accurate?** No. It is heuristic; there can be false positives and false negatives.
8. **Does the app open the URL?** Never. It only analyses the string, so the user is protected from drive-by attacks.
9. **Why Flask?** Lightweight, simple, good for beginners.
10. **Why SQLite?** Serverless, built into Python, ideal for small local apps.
11. **How do you prevent XSS?** Jinja2 auto-escapes all variables.
12. **How to reduce false positives?** Add a whitelist of trusted domains and tune keyword points.
13. **How can ML be added?** Extract URL features (length, dots, digits, HTTPS, keywords) and train a Random Forest classifier; combine its output with the rule score.
14. **What if the QR has multiple codes?** All are decoded and analyzed separately.
15. **What limits does upload have?** PNG/JPG/JPEG only, max 5 MB, processed in memory.

---

# Tanglish Explanation (Simple Tamil + English)

## Project pathi oru line-la
User oru QR code image upload pannuvanga. Namma app athai decode panni, ulla irukura link-a **open pannaama** check pannum. Apram "Safe", "Suspicious", "Dangerous"nu sollum.

## 1. QR decoding eppadi work aagum?
- QR code-nu sonna oru black-white squares pattern. Athula text (URL) hide aagi irukum.
- User upload panna image-a **OpenCV** padikum. Computer-ku image-nu onnum theriyaadhu; athu pixel numbers-oda array dhaan.
- Apram image-a gray color-ku maathum (black & white easy-a detect panna).
- **pyzbar** library QR-oda moonu corner squares-a kandupidichu, black/white dots-a read panni, text-a return pannum.
- pyzbar work aagalana, OpenCV-oda own `QRCodeDetector` backup-a use aagum.
- QR kedaikalana "QR detect aagala"nu friendly error kaatum. Empty-na "QR empty"nu solvom.
- Onnu-ku mela QR irundhaalum ellathaiyum decode pannum.

## 2. URL analysis eppadi work aagum?
Mukkiyamaana rule: **link-a open pannave maatom.** Athu string (text) maathiri dhaan treat pannuvom.
- `extract_url()` - text `http://`, `https://` illa `www.` nu start aana, athu URL. Illana plain text.
- `check_https()` - HTTPS illana risk. (Data encrypt aagaadhu.)
- `is_url_shortener()` - bit.ly, tinyurl maathiri short links real destination-a maraikum, so risk.
- `is_ip_based_url()` - `http://192.168.1.5/login` maathiri IP address irundha suspicious.
- `find_suspicious_keywords()` - login, verify, bank, otp, prize, kyc nu words irundha phishing chance.
- `analyze_domain()` - romba subdomain, romba hyphen, `@` symbol, `.tk/.xyz` maathiri risky extension, romba neenda URL, `paypal` maathiri brand name fake domain-la irundha risk.

## 3. Risk score eppadi calculate aagum?
Ovvoru problem-kum points kudukkirom:
- HTTPS illa = +20
- Shortener = +20
- IP address = +30
- Keyword = ovvonnukum +10 (max 30)
- Fake brand domain = +25
- Vera domain tricks = +10 to +15
- `javascript:` maathiri dangerous scheme = +60

Ellathaiyum kootti (max 100) final score varum. Example: `http://bit.ly/abc` = HTTP (20) + shortener (20) = **40**.
Ithu heuristic (kanakku guess) dhaan, 100% guarantee illa.

## 4. Flask frontend-um backend-um eppadi connect aagum?
- Browser-la `index.html` form irukku. User image select panni "Analyze" click pannuvanga.
- Form `POST /analyze` route-ku image-a anuppum.
- `app.py`-la `@app.route("/analyze")` function image-a vaangi, decode panni, analyze pannum.
- Result-a `render_template("result.html", results=results)` moolama HTML-ku anuppum. Jinja2 `{{ r.score }}` maathiri variables-a fill pannum.
- `/history` route database-la irundhu data eduthu `history.html`-ku kudukum.
- CSS design kudukum; JavaScript animation, image preview, webcam capture handle pannum.

## 5. SQLite history eppadi store pannum?
- App start aagumbodhu `init_db()` `history` table create pannum (illana already irukum).
- Ovvoru analysis mudinjadhum `save_history()` INSERT query use panni id (auto), date/time, QR content, score, result save pannum.
- `?` placeholders use pannuvom, so SQL injection varaadhu.
- `/history` page `SELECT ... ORDER BY id DESC` use panni latest first kaatum.
- Dashboard-la `COUNT(*) ... GROUP BY result` use panni Total, Safe, Suspicious, Dangerous count kaatum.

## 6. Final Safe / Suspicious / Dangerous result eppadi varum?
Score paathu classify pannuvom:
- **0 - 20 = 🟢 SAFE**
- **21 - 50 = 🟡 SUSPICIOUS**
- **51+ = 🔴 DANGEROUS**

Suspicious/Dangerous-na "**Do not open this link until it has been verified**"nu warning kaatum. Safe-nu vandhaalum, "trusted source-a confirm pannunga"nu advice tharum.

## Summary
Image upload -> OpenCV/pyzbar decode -> URL rules check -> points kootu -> Safe/Suspicious/Dangerous decide -> SQLite-la save -> report kaatu. Ithula link eppavume open aagaadhu, adhu dhaan project-oda main security feature.
