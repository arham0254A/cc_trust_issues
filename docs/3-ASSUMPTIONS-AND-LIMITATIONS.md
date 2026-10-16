# Security assumptions and limitations

## Assumptions I rely on
- **I trust the server host and its filesystem.** The SQLite file and
  `PORTAL_SECRET_KEY` are readable only by the app's OS user. Anyone with that
  access owns the app.
- **I assume `PORTAL_SECRET_KEY` is a strong random value in production** and kept
  secret. Session integrity depends entirely on it. The dev fallback is a random
  per-process key, so sessions don't survive a restart.
- **I assume TLS/HTTPS terminates in front of the app** in production, with
  `PORTAL_HTTPS=1` so the session cookie gets the `Secure` flag.
- **I trust admins.** An admin can read members' PII and change roles by design.
- **I assume an ordinary browser** that honours `SameSite`, CSP and `HttpOnly`.
- **I model two threat actors:** an unauthenticated outsider, and a logged-in
  member trying to act outside their role or reach other users' data.

## Known limitations still present in the secure build
- **Brute-force protection is single-node.** Account lockout and the per-IP rate
  limit (`portal/throttle.py`) count attempts in the app's own SQLite database, so
  they don't coordinate across multiple app servers, and an attacker who rotates IP
  addresses can still spray slowly below the per-account threshold.
- **Stateless sessions.** Logout clears the cookie but can't invalidate a copy an
  attacker already exfiltrated before it expires. A server-side session store would
  fix this.
- **No MFA, email verification, or password reset.**
- **No audit logging** of admin actions (role changes, event edits).
- **CSP allows same-origin inline styles via a stylesheet file only**; it's strict
  on scripts but hasn't been tuned with nonces for any future inline needs.
- **SQLite + Flask dev server** suit a local/small deployment, not high concurrency.
  Production needs a WSGI server (gunicorn) and possibly a stronger DB.
- **No SBOM.** Dependency CVE scanning runs in CI (`pip-audit`), but the repo
  doesn't produce a signed software bill of materials.
- **Input validation is server-side and length-bounded**, but there is no formal
  schema validation library; malformed-but-short input is tolerated and ignored.

## Explicitly out of scope
- Network-level attacks (DNS, TLS downgrade), OS hardening, and physical access.
- Denial-of-service resilience beyond a request body size cap.
