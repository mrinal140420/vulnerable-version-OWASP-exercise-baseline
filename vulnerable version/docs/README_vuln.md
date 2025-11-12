# Vulnerable Version (tag: vuln)

**Project:** VulnApp — intentionally vulnerable Flask app  
**Tag:** `vuln`

## How to run (local VM only)
1. ./run.sh
2. flask initdb
3. Open http://127.0.0.1:5000

## Known vulnerabilities (baseline)
- Plaintext passwords (in DB).  
- SQL injection in `/profile/<id>` (string concatenation).  
- IDOR: no server-side authorization on profile access.  
- Admin page accessible without authentication.  
- Insecure file upload → saving user-supplied filenames into web root.  
- No CSRF protection, no secure headers.

