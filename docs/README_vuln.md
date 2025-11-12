# Vulnerable Version (tag: vuln)
This is the intentionally vulnerable baseline used for OWASP exercise scanning.

Known issues:
- Plaintext passwords
- SQL injection / IDOR on /profile/<id>
- Admin page without access control
- Missing CSRF and unsafe redirect 'next'
- Missing security headers (CSP, X-Frame-Options, nosniff)
- Insecure file upload and sensitive files in webroot

Scans:
- Include ZAP report and Nikto output in /scans/
