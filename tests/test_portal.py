from portal.db import get_db


def test_register_and_login(client):
    r = client.post("/auth/register", {"username": "carol", "password": "long-enough-pw"})
    assert r.status_code == 302
    assert client.login("carol", "long-enough-pw").status_code == 302
    assert b"carol (member)" in client.get("/events/").data


def test_register_ignores_role_field(client, app):
    client.post("/auth/register", {"username": "mallory", "password": "long-enough-pw", "role": "admin"})
    with app.app_context():
        role = get_db().execute("SELECT role FROM users WHERE username='mallory'").fetchone()["role"]
    assert role == "member"


def test_wrong_password_rejected(client):
    r = client.login("riya", "nope")
    assert b"Invalid username or password" in r.data


def test_pages_require_login(client):
    for url in ("/events/", "/me/", "/admin/"):
        assert client.get(url).status_code == 302


def test_member_cannot_reach_admin(client):
    client.login("riya")
    assert client.get("/admin/").status_code == 403
    assert client.get("/admin/events/1/attendees").status_code == 403
    assert client.post("/admin/users/1/role", {"role": "admin"}).status_code == 403


def test_admin_dashboard(client):
    client.login("admin")
    assert client.get("/admin/").status_code == 200


def test_profile_edit_only_touches_own_row_and_not_role(client, app):
    client.login("riya")
    client.post("/me/", {"full_name": "Riya A", "email": "a@x.io", "bio": "hi", "role": "admin", "id": "2"})
    with app.app_context():
        rows = {r["username"]: r for r in get_db().execute("SELECT * FROM users")}
    assert rows["riya"]["full_name"] == "Riya A"
    assert rows["riya"]["role"] == "member"
    assert rows["aditya"]["full_name"] == ""


def test_event_capacity_and_unregister(client, app):
    client.login("riya")
    client.post("/events/1/register")
    other = type(client)(app)
    other.login("aditya")
    r = other.post("/events/1/register")
    assert b"Could not register" in other.get("/events/1").data or r.status_code == 302
    other.post("/events/1/unregister")
    with app.app_context():
        n = get_db().execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    assert n == 1


def test_post_without_csrf_token_rejected(client):
    client.login("riya")
    assert client.post("/me/", {"bio": "x"}, token=False).status_code == 400


def test_security_headers(client):
    r = client.get("/auth/login")
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Frame-Options"] == "DENY"


def test_open_redirect_blocked(client):
    data = {"username": "riya", "password": "correct-horse", "csrf_token": client.token()}
    r = client.c.post("/auth/login?next=https://evil.example", data=data)
    assert r.headers["Location"] == "/events/"
