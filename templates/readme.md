# Vulnerable Flask App Skeleton


**WARNING**: This intentionally vulnerable app is for learning only. Run locally in a VM or Docker and do NOT expose to public networks.


## Run
1. ./run.sh
2. flask initdb
3. Visit http://127.0.0.1:5000


## Vulnerabilities included
- Plaintext passwords
- SQL injection via /profile/<id>
- IDOR (no server-side authorization)
- Insecure file upload
- Admin page accessible without auth


Fix these as part of the hardening exercise.