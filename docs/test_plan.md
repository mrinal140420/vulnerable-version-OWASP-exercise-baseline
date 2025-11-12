# Test Plan
1. Run ZAP scan before/after and compare alerts.
2. Run nikto -h http://127.0.0.1:5000 to confirm sensitive files removed.
3. Run gobuster to check endpoints.
4. Manual tests:
   - login CSRF test
   - IDOR test (alice accessing bob)
   - upload allowed/disallowed files
   - cookie/header checks via curl -I
