# Remediation Report (summary)
- Plaintext passwords -> Fixed: hashed passwords (werkzeug)
- SQLi/IDOR -> Fixed: ORM + owner/admin check on /profile/<id>
- Admin page open -> Fixed: login + is_admin check
- Missing CSRF -> Fixed: Flask-WTF CSRFProtect + csrf_token
- Missing headers -> Fixed: Flask-Talisman (CSP, X-Frame-Options, nosniff, HSTS)
- Sensitive files -> Removed from webroot, rotated credentials
- Uploads insecure -> Fixed: whitelist, random names, admin-only listing
