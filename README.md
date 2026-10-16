# Club Portal — "Trust Issues" task

A small Flask + SQLite portal for a college club: member accounts, profiles, event
registration, and an admin area, with two roles (`member` and `admin`). I built it
for the CC-VIT "Trust Issues" task: an intentionally vulnerable web app, the exploits
against it, and a hardened version that fixes them.

## Deliverables

| Deliverable | Where |
|-------------|-------|
| Vulnerable + secured source | `vulnerable` branch vs `main` (same `portal/` package) |
| Each vulnerability: root cause + remediation | [docs/1-SECURITY-ASSESSMENT-REPORT.md](docs/1-SECURITY-ASSESSMENT-REPORT.md) |
| Proof-of-concept demonstrations | [exploits/poc.py](exploits/poc.py) + [screenshots/](screenshots/) |
| Security assessment report | [docs/1-SECURITY-ASSESSMENT-REPORT.md](docs/1-SECURITY-ASSESSMENT-REPORT.md) |
| Threat model | [docs/2-THREAT-MODEL.md](docs/2-THREAT-MODEL.md) |
| Setup + testing instructions | this README |

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/flask --app portal init-db
.venv/bin/flask --app portal create-admin admin        # prompts for a password
PORTAL_SECRET_KEY=$(python3 -c 'import secrets;print(secrets.token_hex(32))') \
  .venv/bin/flask --app portal run
```

Open http://127.0.0.1:5000, register a member account, and log in as `admin` in
another browser to create events.

## Tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
```

(`PYTEST_DISABLE_PLUGIN_AUTOLOAD` stops system-wide pytest plugins from interfering.)

## Two versions: secure (`main`) vs vulnerable (`vulnerable` branch)

I keep both a vulnerable app and a fixed one so the attacks can be shown working and
then blocked. They are the same `portal/` package on two git branches, so `git diff`
shows every fix as a clean changeset:

| Branch | State | Purpose |
|--------|-------|---------|
| `main` | secured / hardened | the real app; deploy this |
| `vulnerable` | deliberately broken | the exploit target; never deploy |

```bash
git checkout vulnerable     # the insecure build
git checkout main           # the fixed build
git diff vulnerable main    # every security fix, as a diff
```

Each flaw on the `vulnerable` branch is tagged `# VULN #1`..`#5` in the source and
maps to its fix on `main`. I write up all five in the assessment report.

### Attack the vulnerable build

```bash
git checkout vulnerable
PYTHONPATH= .venv/bin/flask --app portal init-db          # seeds admin/riya/aditya
PYTHONPATH= .venv/bin/flask --app portal run --port 5001  # terminal 1
.venv/bin/python exploits/poc.py                          # terminal 2 -> all EXPLOITABLE
```

Seeded logins (vulnerable branch): `admin` / `SuperSecretAdmin1`, `riya` / `riyapassword`.

### Prove the fixes hold (secure build)

```bash
git checkout main
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
```

`tests/test_security_regression.py` replays each exploit against the secure app and
asserts it is blocked.

## Documentation (`docs/`)

| File | Contents |
|---|---|
| `1-SECURITY-ASSESSMENT-REPORT.md` | The main write-up: each vulnerability, how I built it, its impact, and the fix, with screenshots |
| `2-THREAT-MODEL.md` | Assets, actors, trust boundaries, STRIDE |
| `3-ASSUMPTIONS-AND-LIMITATIONS.md` | Security assumptions and remaining limits |

## Layout

| Path | What it is |
|---|---|
| `portal/__init__.py` | App factory: config, cookie flags, loads the current user each request |
| `portal/security.py` | `login_required`, `role_required`, CSRF tokens, security headers |
| `portal/auth.py` | Register / login / logout |
| `portal/members.py` | Own-profile view and edit |
| `portal/events.py` | Event list, detail, register / unregister |
| `portal/admin.py` | Admin dashboard, attendees, create event, change roles |
| `portal/throttle.py` | Account lockout + per-IP login rate limiting |
| `portal/schema.sql` | Tables: `users`, `events`, `registrations`, `login_attempts` |
| `tests/` | Feature, access-control, and security-regression tests |
| `exploits/poc.py` | Scripted proof-of-concept attacks |
| `screenshots/` | Proof-of-concept evidence |

## Bonus features

| Bonus | Where |
|-------|-------|
| Automated security regression tests | `tests/test_security_regression.py` |
| Rate limiting + account lockout | `portal/throttle.py`, `portal/auth.py`; tests in `tests/test_bruteforce.py` |
| Role-based access control (+ ownership checks) | `portal/security.py` (`role_required`) |
| Secure cookies, security headers, input validation | `portal/__init__.py`, `portal/security.py` |
| Threat model | `docs/2-THREAT-MODEL.md` |
| Security scanning in CI | `.github/workflows/ci.yml` (pytest + Bandit + pip-audit) |

### Run the security scanners locally

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/bandit -r portal                 # clean on main, flags the vulnerable branch
.venv/bin/pip-audit -r requirements.txt    # dependency CVE audit
```
