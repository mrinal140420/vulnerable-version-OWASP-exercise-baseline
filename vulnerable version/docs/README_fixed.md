# Hardened Version (tag: fixed)

**Project:** VulnApp — hardened version  
**Tag:** `fixed`

## Key fixes applied
- Replaced plaintext passwords with salted hashes (werkzeug / bcrypt).  
- Parameterized SQL / migrated to ORM queries (no string concatenation).  
- Enforced server-side authorization checks for `/profile/<id>`.  
- Admin page protected (login + role check).  
- File uploads validated (whitelist extensions) and stored outside web root with secure random names.  
- Added secure cookie flags (HttpOnly, Secure, SameSite).  
- Disabled debug mode, added basic CSP/HSTS via Talisman.  
- Removed or restricted default endpoints and added rate-limiting on auth.

## How to run
(same as vuln; note: uses hardened config)
