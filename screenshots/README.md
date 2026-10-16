# Screenshots

Proof-of-concept evidence, captured against the vulnerable build on port 5001.
The assessment report ([../docs/8-SECURITY-ASSESSMENT-REPORT.md](../docs/8-SECURITY-ASSESSMENT-REPORT.md))
references the primary file for each vulnerability (`01`–`05`); the lettered files
are the supporting steps.

## Placed

| File | What it shows |
|------|---------------|
| `01-sqli-login.png` | Login form with username `admin' --` and a throwaway password |
| `01b-sqli-logged-in.png` | Result: logged in as `admin (admin)` with no valid password |
| `02a-register-curl.png` | `curl` registering `evil` with an extra `role=admin` field |
| `02b-login-as-evil.png` | Logging in as the `evil` account |
| `02-mass-assignment.png` | Admin dashboard as `evil (admin)` — a self-registered admin |
| `02c-evil-events.png` | `evil` sees the Admin link; it's a full admin |
| `03a-own-profile.png` | `riya` viewing her own profile at `/me/user/2` |
| `03-idor.png` | `riya` viewing `aditya`'s profile at `/me/user/3` (IDOR) |
| `04b-no-admin-link.png` | `riya` (member) has no Admin link in the menu |
| `04-broken-access.png` | ...but `riya` (member) opens `/admin/` directly anyway |
| `04a-self-promote.png` | `riya` used the role control to make herself admin ("Role updated") |
| `05a-plant-payload.png` | `aditya` sets his full name to a `<script>` payload |
| `05b-rendered-name.png` | Admin dashboard renders the payload — name shows as bold `pwned` |
| `05-stored-xss.png` | The script runs in the admin's browser; the alert leaks the session cookie |
| `06-poc-run.png` | `exploits/poc.py` summary: all five report `EXPLOITABLE` |
| `07-tests-pass.png` | `pytest` on `main`: `19 passed` |
| `08-bandit.png` | Bandit clean on `main` (`exit: 0`), flagging the vulnerable build |
| `08b-bandit-detail.png` | The vulnerable Bandit run in full: SQL-injection + hard-coded secret, `exit: 1` |

