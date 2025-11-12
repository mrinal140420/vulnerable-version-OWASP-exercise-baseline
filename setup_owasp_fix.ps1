# setup_owasp_fix.ps1
# Hardened + Vulnerable version management script for OWASP exercise
# Author: Mrinal Sahoo
# Run from your project root folder (where app.py etc. exist)

Write-Host "=== OWASP Git Automation Script ==="

# --- Configuration ---
$remote = "https://github.com/mrinal140420/vulnerable-version-OWASP-exercise-baseline.git"

# --- Check Git availability ---
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git is not installed or not in PATH. Please install Git first."
    exit
}

# --- Initialize Git repo if needed ---
if (-not (Test-Path ".git")) {
    git init | Out-Null
    Write-Host "Initialized new git repository"
} else {
    Write-Host "Git repo already initialized"
}

# --- Set remote ---
try {
    git remote remove origin | Out-Null
} catch {}
git remote add origin $remote
Write-Host "Set remote to $remote"

# --- Commit vulnerable version ---
git checkout -B vuln-version
git add .
git commit -m "vuln: initial vulnerable Flask app baseline" 2>$null
git tag -a vuln -m "vuln: vulnerable baseline for OWASP exercise"
Write-Host "Vulnerable version committed and tagged as 'vuln'"

# --- Push vulnerable version ---
git push -u origin vuln-version
git push origin vuln
Write-Host "Pushed vuln-version branch and tag"

# --- Create fix branch ---
git checkout -B hardening-fix vuln-version
Write-Host ""
Write-Host "Now replace vulnerable files with the hardened versions (as provided)."
Read-Host "Press Enter after you have replaced and saved the fixed files..."

# --- Commit fixed version ---
git add .
git commit -m "fix: harden app - password hashing, CSRF, secure headers, upload hardening, auth checks" 2>$null
git tag -a fixed -m "fixed: hardened version (OWASP remediations applied)"
Write-Host "Fixed version committed and tagged as 'fixed'"

# --- Push fixed version ---
git push -u origin hardening-fix
git push origin fixed
Write-Host "Pushed hardening-fix branch and fixed tag"

# --- Create docs directory ---
if (-not (Test-Path "docs")) {
    New-Item -ItemType Directory -Path "docs" | Out-Null
}
Write-Host "Created docs/ directory"

# --- Create documentation files (plain ASCII) ---
$readmeVuln = @"
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
"@

$readmeFixed = @"
# Hardened Version (tag: fixed)
Hardened app with following primary fixes:
- Password hashing (werkzeug)
- ORM-based queries and server-side authorization
- Admin access restricted to admin users
- CSRF protection added
- Secure headers (CSP, X-Frame-Options, nosniff, HSTS)
- Uploads whitelisted and stored with random filenames
- Server header suppressed
"@

$remediation = @"
# Remediation Report (summary)
- Plaintext passwords -> Fixed: hashed passwords (werkzeug)
- SQLi/IDOR -> Fixed: ORM + owner/admin check on /profile/<id>
- Admin page open -> Fixed: login + is_admin check
- Missing CSRF -> Fixed: Flask-WTF CSRFProtect + csrf_token
- Missing headers -> Fixed: Flask-Talisman (CSP, X-Frame-Options, nosniff, HSTS)
- Sensitive files -> Removed from webroot, rotated credentials
- Uploads insecure -> Fixed: whitelist, random names, admin-only listing
"@

$testPlan = @"
# Test Plan
1. Run ZAP scan before/after and compare alerts.
2. Run nikto -h http://127.0.0.1:5000 to confirm sensitive files removed.
3. Run gobuster to check endpoints.
4. Manual tests:
   - login CSRF test
   - IDOR test (alice accessing bob)
   - upload allowed/disallowed files
   - cookie/header checks via curl -I
"@

# Write files
$readmeVuln | Out-File -FilePath docs\README_vuln.md -Encoding UTF8
$readmeFixed | Out-File -FilePath docs\README_fixed.md -Encoding UTF8
$remediation | Out-File -FilePath docs\remediation_report.md -Encoding UTF8
$testPlan | Out-File -FilePath docs\test_plan.md -Encoding UTF8

git add docs/*
git commit -m "docs: add README_vuln, README_fixed, remediation report, and test plan" 2>$null

# --- Generate remediation diff ---
try {
    git diff vuln fixed > docs\remediation_patch.diff
    git add docs\remediation_patch.diff
    git commit -m "docs: add remediation_patch.diff" 2>$null
} catch {
    Write-Host "Could not generate diff; ensure tags 'vuln' and 'fixed' exist." -ForegroundColor Yellow
}

# --- Push docs and tags ---
git push origin hardening-fix
git push origin --tags
Write-Host "Documentation and remediation patch pushed"

Write-Host ""
Write-Host "=== All done! ==="
Write-Host "Vulnerable and fixed versions should be on GitHub (tags: vuln, fixed)."
