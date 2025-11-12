# Remediation Report — Vulnerable Flask App

Author: Mrinal  
Date: 2025-11-12

## Finding 1 — Plaintext passwords
- Severity: High
- Evidence: profile page showed plaintext password in template (vuln). (original profile template). :contentReference[oaicite:6]{index=6}
- Fix: Hash passwords using `werkzeug.security.generate_password_hash` and `check_password_hash`. Seeded DB uses hashed values.
- Verification:
  - Run `sqlite3 app.db "select username,password from user;"` — passwords now show `$pbkdf2:...`
  - Login with known creds (admin/admin) still works.

## Finding 2 — SQL injection & IDOR on `/profile/<id>`
- Severity: Critical
- Evidence: raw SQL concatenation in `app.py` (original). :contentReference[oaicite:7]{index=7}
- Fix: Replaced raw SQL with ORM `User.query.get(uid)` and added server-side authorization (owner or admin only).
- Verification:
  - Attempt `GET /profile/1' OR '1'='1` — returns 404 or blocked.
  - Login as alice and access `/profile/2` → gets 403.

## Finding 3 — Admin page publicly accessible
- Severity: High
- Evidence: `admin.html` was served without auth (original). :contentReference[oaicite:8]{index=8}
- Fix: `@login_required` + `if not current_user.is_admin: abort(403)` guard added.
- Verification:
  - Unauthenticated user visiting `/admin` gets redirected to login.
  - Non-admin authenticated user gets 403.

## Finding 4 — Missing CSRF & unsafe redirect `next`
- Severity: High
- Evidence: login form had no CSRF token; `next` param not validated. 
- Fix: Added `Flask-WTF` CSRFProtect and `{{ csrf_token() }}` in templates. Implemented `is_safe_url()` check for redirect next.
- Verification:
  - POST to login without CSRF fails.
  - Malicious `next` to external host is sanitized and ignored.

## Finding 5 — Security headers & Server version leak
- Severity: Medium
- Evidence: ZAP report flagged missing CSP, X-Frame-Options, X-Content-Type-Options and Server header leak. 
- Fix: Added Flask-Talisman to set CSP, X-Frame-Options=DENY, X-Content-Type-Options=nosniff, HSTS. Suppress Server header.
- Verification:
  - `curl -I http://127.0.0.1:5000` shows expected headers.

## Finding 6 — Insecure file upload & public serving of uploads
- Severity: High
- Evidence: upload template indicated files stored under static/uploads and listed publicly. :contentReference[oaicite:11]{index=11}
- Fix:
  - Whitelist allowed extensions.
  - Save files with random UUID names.
  - Only admins can view/download uploaded files.
- Verification:
  - Try uploading disallowed extension (e.g., `.php`) → rejected.
  - Uploaded files get random UUID names; non-admin cannot access `/uploads/<file>`.

## Finding 7 — wp-config.php discovered by Nikto
- Severity: Critical
- Evidence: Nikto output included `wp-config.php` discovery. (file uploaded earlier). :contentReference[oaicite:12]{index=12}
- Fix:
  - Remove from webroot and rotate any exposed credentials.
  - Add server rule to deny access to config/backups.
- Verification:
  - Re-run Nikto → `wp-config.php` not found.

