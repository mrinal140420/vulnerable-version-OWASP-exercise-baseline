# Vulnerable → Hardened OWASP Exercise (Flask)

**Project:** OWASP Exercise — Vulnerable baseline + Hardened version  
**Repo:** `vulnerable-version-OWASP-exercise-baseline`  
**Author:** Mrinal Sahoo  
**Date:** 2025-11-12

---

## Table of contents

1. [Project overview](#project-overview)  
2. [Goals & learning objectives](#goals--learning-objectives)  
3. [Repository layout](#repository-layout)  
4. [Prerequisites & dependencies](#prerequisites--dependencies)  
5. [Quickstart — run vulnerable baseline (safe VM)](#quickstart--run-vulnerable-baseline-safe-vm)  
6. [Quickstart — run hardened version](#quickstart--run-hardened-version)  
7. [Scanning & verification commands (ZAP / Nikto / Gobuster / Suricata / ClamAV)](#scanning--verification-commands-zap--nikto--gobuster--suricata--clamav)  
8. [Findings & remediation summary (high level)](#findings--remediation-summary-high-level)  
9. [Remediation report structure & evidence to collect](#remediation-report-structure--evidence-to-collect)  
10. [Test plan (automated + manual)](#test-plan-automated--manual)  
11. [Deliverables you must produce](#deliverables-you-must-produce)  
12. [Security & safety notes (must-read)](#security--safety-notes-must-read)  
13. [Troubleshooting & rollback](#troubleshooting--rollback)  
14. [Contact / authorship / acknowledgements](#contact--authorship--acknowledgements)

---

## Project overview

This repository contains two states of a small Flask-based web application used for learning OWASP Top 10 and secure development practices:

- **Vulnerable baseline** (`vuln` tag/branch) — intentionally insecure to exercise detection and exploitation.  
- **Hardened / fixed version** (`fixed` tag/branch) — demonstrates fixes, secure configuration, and verification.

> **IMPORTANT:** Run everything in an **isolated local VM or Docker container**. Do **not** expose the vulnerable baseline to public networks.

---

## Goals & learning objectives

- Understand common web vulnerabilities: **SQLi**, **IDOR**, **CSRF**, **insecure uploads**, **information leakage**.  
- Use scanning tools: **OWASP ZAP**, **Nikto**, **Gobuster**, **Suricata**, **ClamAV**.  
- Apply fixes and hardening: password hashing, CSRF protection, secure headers, upload hardening.  
- Produce reproducible deliverables: `vuln`/`fixed` tags, remediation diff, scan reports, remediation report, and a test plan.

---

## Repository layout

```
/
├── app.py                        # Flask application (vulnerable or fixed depending on tag)
├── app.db                        # SQLite DB (do not commit secrets)
├── requirements.txt
├── run.sh
├── setup_owasp_fix.ps1           # (optional) automation script
├── templates/                    # Jinja2 templates
│   ├── base.html
│   ├── login.html
│   ├── profile.html
│   ├── admin.html
│   └── upload.html
├── static/uploads/               # uploads (ensure not world-writeable)
├── scans/                        # store scanner outputs: ZAP, Nikto, Gobuster
├── docs/
│   ├── README_vuln.md
│   ├── README_fixed.md
│   ├── remediation_report.md
│   ├── test_plan.md
│   └── remediation_patch.diff
└── README.md                     # this file
```

---

## Prerequisites & dependencies

**Host:** Local VM (recommended Ubuntu 22.04 / Debian 12) or Docker container.

### System packages (Ubuntu / Debian example)
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl nikto gobuster clamav suricata
```

### Python dependencies (inside virtualenv)
```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` **should** include:
```
Flask
Flask-Login
Flask-SQLAlchemy
Flask-WTF
flask-talisman
werkzeug
```

> **Do not** commit secrets (API keys, plaintext passwords, private keys). Keep `app.db` and `.env` out of public repos.

---

## Quickstart — run vulnerable baseline (safe VM)

> **NOTE:** do not expose port `5000` to the public Internet. Use `127.0.0.1` binding or container networking.

1. Start a VM snapshot (so you can revert later).

2. Clone the repo and checkout the vulnerable tag/branch:
```bash
git clone https://github.com/mrinal140420/vulnerable-version-OWASP-exercise-baseline.git
cd vulnerable-version-OWASP-exercise-baseline
git checkout vuln-version   # or: git checkout tags/vuln
```

3. Setup virtualenv and install dependencies:
```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

4. Initialize DB (if included):
```bash
flask initdb   # or python3 app.py
```

5. Run the app (bind to localhost):
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=127.0.0.1 --port=5000

# or
python3 app.py
```

6. Run scans (see “Scanning & verification” below) and save outputs to `scans/`.

---

## Quickstart — run hardened version

1. Switch to the hardened branch/tag (after fixes are committed):
```bash
git checkout hardening-fix   # or: git checkout tags/fixed
```

2. Activate venv and ensure dependencies:
```bash
. venv/bin/activate
pip install -r requirements.txt
```

3. Reinitialize DB if required (hardened seed will include hashed passwords):
```bash
flask initdb
python3 app.py
```

4. Re-run scans and compare results (ZAP / Nikto / Gobuster). Previously flagged findings should be reduced or absent.

---

## Scanning & verification commands (ZAP / Nikto / Gobuster / Suricata / ClamAV)

> Save all scanner outputs under `scans/`. Use `*-before` and `*-after` naming for clear comparisons.

### OWASP ZAP
- Use the ZAP GUI or headless mode to spider + active-scan.
- Proxy your browser through ZAP to exercise authenticated flows, then run active scan.
- Save HTML / XML reports to `scans/zap/`.

### Nikto
```bash
nikto -h http://127.0.0.1:5000 -output scans/nikto-before.txt
# after fixes:
nikto -h http://127.0.0.1:5000 -output scans/nikto-after.txt
```

### Gobuster (directory discovery)
```bash
gobuster dir -u http://127.0.0.1:5000 -w /usr/share/seclists/Discovery/Web-Content/common.txt -t 50 -o scans/gobuster-before.txt
```

### Header checks (curl)
```bash
curl -I http://127.0.0.1:5000

# expected (after fixes):
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Content-Security-Policy: default-src 'self'
# Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

### Cookie verification
```bash
curl -I -L http://127.0.0.1:5000/login
# check Set-Cookie includes HttpOnly; SameSite=Lax (or Strict); Secure (when HTTPS)
```

### Suricata (IDS) — optional
```bash
sudo apt install suricata

# add to /etc/suricata/rules/local.rules:
# alert http any any -> any any (msg:"HTTP GET to /admin detected"; http_uri; content:"/admin"; sid:1000001; rev:1;)

sudo systemctl restart suricata

# trigger
curl http://127.0.0.1:5000/admin
sudo tail -n 200 /var/log/suricata/fast.log
```

---

## Findings & remediation summary (high level)

**High / Critical**
- **SQL Injection / IDOR** on `/profile/<id>`  
  _Fix:_ Use SQLAlchemy ORM / parameterized queries + strict authorization checks (non-admin users blocked).

- **Plaintext passwords stored**  
  _Fix:_ Use `werkzeug.security.generate_password_hash` + `check_password_hash`.

- **Exposed config or backup files in webroot (e.g., `wp-config.php`)**  
  _Fix:_ Remove from webroot; rotate any leaked credentials; add `.gitignore`.

- **Insecure file upload** (arbitrary filenames, executable uploads)  
  _Fix:_ Whitelist extensions, validate MIME types, randomize stored filenames, restrict upload directory permissions, limit file sizes, restrict functionality to admin users.

**Medium**
- Missing CSRF protection on forms  
  _Fix:_ Enable `Flask-WTF` CSRFProtect.

- Missing security headers: CSP, X-Content-Type-Options, X-Frame-Options, HSTS  
  _Fix:_ Add `flask-talisman` or set headers manually.

- Cookies missing `SameSite`/`HttpOnly`/`Secure` flags  
  _Fix:_ Configure `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`, set `Secure=True` when using TLS.

**Low**
- Server header leaking Werkzeug/Python  
  _Fix:_ Suppress in Flask (or run behind a hardened proxy) to avoid information leakage.

- Verbose error messages  
  _Fix:_ Set `DEBUG=False` and handle errors gracefully.

---

## Remediation report structure & evidence to collect

For each finding, include:

1. **Finding title**  
2. **Severity** (Critical / High / Medium / Low)  
3. **Evidence** — raw scanner output, curl output, screenshots (link to `scans/` or `docs/images/`)  
4. **Fix applied** — code snippet + commit hash  
5. **Verification** — commands + output showing the fix

**Example evidence files to attach:**
- `scans/zap/2025-11-12-ZAP-Report.html` (before) and `scans/zap/after.html`  
- `scans/nikto-before.txt` and `scans/nikto-after.txt`  
- `scans/gobuster-before.txt` and `scans/gobuster-after.txt`  
- `docs/remediation_patch.diff` (git diff between `vuln` and `fixed`)

---

## Test plan (automated + manual)

### Automated
- ZAP active scan (before / after)  
- Nikto scan (before / after)  
- Gobuster directory discovery (before / after)  
- ClamAV scan (EICAR) and optional YARA tests (lab only)

### Manual
- **SQLi / IDOR:** Log in as a normal user (`alice`), request `/profile/<bob-id>` → expect `403` or redirect.  
- **CSRF:** POST to endpoints without CSRF token → expect rejection (`400`/`403`).  
- **Upload:** Attempt to upload disallowed extension (e.g., `.php`) → must be rejected.  
- **Headers:** `curl -I` to confirm security headers & cookie flags.  
- **Sensitive files:** Attempt to download known backups from webroot → expect `404`/`403`.
---

## Security & safety notes (must-read)

- **Always** run the vulnerable baseline inside an isolated VM (snapshot before starting). Do **not** connect the VM to production networks.  
- Remove sensitive files and credentials from the repo before pushing (`.gitignore` your DB and `.env`).  
- If real credentials are discovered (e.g., in `wp-config.php`), **rotate credentials immediately**.  
- After exercises, revert the VM snapshot or destroy the VM to avoid leaving a vulnerable instance.  
- Never scan or attack systems you do not own or do not have explicit authorization to test.

---

## Troubleshooting & rollback

**Common fixes**
- If `pip install -r requirements.txt` fails, upgrade pip:
```bash
python3 -m pip install --upgrade pip
```
- If port `5000` is in use:
```bash
lsof -i :5000
# kill the process or choose a different port
```

**Git rollback**
```bash
# rollback last local commit
git reset --hard HEAD~1

# recreate tags if needed
git tag -f vuln <commit-hash>
git tag -f fixed <commit-hash>
git push --force origin vuln fixed
# CAUTION: only force-push to personal repos
```

---

## Contact / authorship / acknowledgements

**Author:** Mrinal Sahoo

Developed as a learning exercise for OWASP Top 10 and system hardening.  
Thanks to OWASP Juice Shop, Nikto, OWASP ZAP, Gobuster, Suricata, and ClamAV for tools and inspiration.

---

## Quick copy-paste checklists

### Before running vuln baseline
```bash
# snapshot VM
git clone https://github.com/mrinal140420/vulnerable-version-OWASP-exercise-baseline.git
cd vulnerable-version-OWASP-exercise-baseline
git checkout vuln-version
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
flask initdb || true
flask run --host=127.0.0.1 --port=5000
```

### Run basic scans
```bash
nikto -h http://127.0.0.1:5000 -output scans/nikto-before.txt
gobuster dir -u http://127.0.0.1:5000 -w /usr/share/seclists/Discovery/Web-Content/common.txt -o scans/gobuster-before.txt
curl -I http://127.0.0.1:5000 | tee scans/headers-before.txt
```

### After fixes
```bash
git checkout hardening-fix
. venv/bin/activate
pip install -r requirements.txt
flask initdb || true
python3 app.py
# re-run scans into *-after files
```

---

## Templates & examples to include in `docs/` (suggested)

### `docs/remediation_report.md` — suggested structure
```
# Remediation Report

## Finding: SQL Injection / IDOR on /profile/<id>
- Severity: High
- Evidence:
  - scans/zap/sql-injection-report.html
  - scans/nikto-before.txt (relevant lines)
- Fix applied:
  - commit: <hash>
  - summary: migrated raw SQL to SQLAlchemy ORM and added ownership checks
  - code snippet:
```py
# example
user = User.query.get_or_404(profile_id)
if user.id != current_user.id and not current_user.is_admin:
    abort(403)
```
- Verification:
  - curl -I http://127.0.0.1:5000/profile/2  # as alice -> 403
  - scans/nikto-after.txt
```

### `docs/test_plan.md` — suggested entries
```
# Test Plan

## Automated tests
- ZAP active scan: run before/after, save HTML report
- Nikto scan: run before/after, save outputs
- Gobuster: run before/after for directory discovery

## Manual tests
- IDOR: using two user accounts, verify resource access controls
- CSRF: attempt form POST without CSRF token
- Upload: attempt .php upload and confirm rejection
- Cookie flags: inspect Set-Cookie headers for HttpOnly, Secure, SameSite
```
.
