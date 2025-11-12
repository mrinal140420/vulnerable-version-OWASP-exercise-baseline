# Test Plan — Hardened App Verification

## Automated scans
1. Run ZAP full scan (same profile used before). Expect previous header/CSRF/IDOR alerts resolved.
2. Run Nikto:
   nikto -h http://127.0.0.1:5000 -output scans/nikto-after.txt
   grep -i wp-config scans/nikto-after.txt  # should print nothing

3. Run Gobuster:
   gobuster dir -u http://127.0.0.1:5000 -w /usr/share/seclists/Discovery/Web-Content/common.txt -o scans/gobuster-after.txt

## Manual tests / verification steps
1. Header check:
   curl -I http://127.0.0.1:5000
   - Expect: X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Content-Security-Policy present, Strict-Transport-Security present.

2. Cookie flags:
   curl -I -L http://127.0.0.1:5000/login
   - Expect Set-Cookie includes HttpOnly and SameSite=Lax (Secure when TLS enabled).

3. CSRF test:
   - Attempt to POST to /login (or other state-change) without CSRF token → should be rejected (400/403).

4. IDOR / SQLi:
   - Login as alice, hit /profile/2 (bob) → expect 403.
   - Try SQLi payload in profile id → should not return data.

5. Admin access:
   - Unauthenticated: /admin → redirect to login.
   - Authenticated non-admin: /admin → 403.
   - Admin: /admin → list users.

6. Upload tests:
   - Upload allowed file type → success; filename randomized.
   - Upload disallowed type .php → rejected.
   - Non-admin cannot list or download uploads.

7. Nikto/Gobuster:
   - Re-run scans to confirm removed sensitive files & endpoints.

## Evidence to collect
- ZAP HTML report (after) and before (for comparison).
- Nikto after output.
- Gobuster after output.
- curl -I outputs (headers).
- Screenshots: login with CSRF token present, upload flow, admin access 403 for non-admin.
- Git diff / remediation_patch.diff showing exact code changes.
