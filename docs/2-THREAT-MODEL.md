# Threat model — Club Portal

My threat model: what I protect, who might attack, where the trust boundaries
are, and how the secure build (`main`) addresses each threat. I use STRIDE as a
checklist.

## 1. Assets (what I protect)

| Asset | Why it matters |
|-------|----------------|
| User credentials (password hashes) | Account takeover; users reuse passwords elsewhere |
| Session cookies | A stolen session = acting as that user |
| Member PII (name, email) | Privacy; the club has a duty of care |
| Role / authorization state | Admin access is the keys to the kingdom |
| Event & registration data | Integrity of who's coming to what |
| `SECRET_KEY` | Signs sessions; leak = forge any session |

## 2. Actors / threat agents

- **Unauthenticated outsider** — anyone on the network who can reach the site.
- **Authenticated member** — a logged-in low-privilege user trying to act above
  their role or reach other users' data. (The most important actor for this task.)
- **Malicious/curious admin** — trusted by design, but see assumptions.
- **Attacker's website** — a third-party page trying to abuse the victim's browser
  (CSRF, clickjacking) while the victim is logged in.

Out of scope: nation-state, physical access, insider with server/OS access, DoS.

## 3. Trust boundaries & attack surface

```
   [ Browser ]  --HTTP(S)-->  [ Flask app ]  -->  [ SQLite file ]
        ^                          ^                     ^
   untrusted input           enforces authZ         trusted store
   (forms, URL, cookies)      here, server-side
```

Every arrow crossing into the app is attack surface:

| Surface | Entry points | Primary risks |
|---------|-------------|---------------|
| Login / register | `/auth/*` | Injection, brute force, user enumeration, mass assignment |
| Profile | `/me/` | IDOR, stored XSS, mass assignment |
| Events | `/events/*` | Broken access control, race conditions on capacity |
| Admin | `/admin/*` | Broken access control / privilege escalation |
| Session cookie | every request | Forgery, theft, fixation |
| Any POST | all forms | CSRF |

## 4. STRIDE → threats → mitigations (secure build)

| STRIDE | Threat here | Mitigation in `portal/` |
|--------|-------------|--------------------------|
| **S**poofing | Log in as someone else | Salted scrypt password hashing; generic login error; new session on login (anti-fixation); signed session cookie |
| **T**ampering | Change role/id/other users' data via forms or URLs | Parameterised SQL; role & ids read server-side (session), not from client; field allow-lists; CSRF tokens |
| **R**epudiation | "I didn't do that" | *Partial* — no audit log yet (see limitations) |
| **I**nfo disclosure | Read others' PII, enumerate users | `role_required` on admin; ownership-scoped queries; identical login responses; escaped output |
| **D**enial of service | Brute-force / spam login | Account lockout + per-IP rate limit; request body size cap |
| **E**levation of privilege | Member becomes admin | Role from DB each request; `role_required`; role never client-settable; admins only via CLI/existing admin |

## 5. How the five demonstrated vulnerabilities map here

Each flaw I built on the `vulnerable` branch is one of these threats realised, and
its fix is the mitigation above:

- SQL injection → Spoofing/Tampering → parameterised queries.
- Mass assignment → Elevation of privilege → role not client-controlled.
- IDOR → Information disclosure/Tampering → ids from session.
- Broken access control → Elevation of privilege → `role_required`.
- Stored XSS → Tampering/Info disclosure → auto-escaping + CSP.

## 6. Residual risk

See `docs/3-ASSUMPTIONS-AND-LIMITATIONS.md`. The notable gaps are: no audit
logging (Repudiation), stateless sessions I can't revoke before expiry, and no
MFA. I accept these for a small, locally-hosted club portal and flag them for a
production hardening pass.
