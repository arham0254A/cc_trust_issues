from portal.db import get_db


def test_sqli_login_is_not_exploitable(client):
    r = client.post("/auth/login", {"username": "admin' --", "password": "anything"})
    assert b"Invalid username or password" in r.data
    assert client.get("/events/").status_code == 302


def test_registration_cannot_grant_admin(client, app):
    client.post("/auth/register", {"username": "evil2", "password": "whatever10", "role": "admin"})
    with app.app_context():
        role = get_db().execute("SELECT role FROM users WHERE username='evil2'").fetchone()["role"]
    assert role == "member"


def test_no_idor_endpoint_and_edits_touch_only_self(client, app):
    client.login("riya")
    assert client.get("/me/user/3").status_code == 404
    client.post("/me/", {"full_name": "Riya", "email": "a@x.io", "bio": "hi"})
    with app.app_context():
        aditya = get_db().execute("SELECT full_name FROM users WHERE username='aditya'").fetchone()
    assert aditya["full_name"] == ""


def test_member_cannot_reach_or_use_admin(client):
    client.login("riya")
    assert client.get("/admin/").status_code == 403
    assert client.post("/admin/users/1/role", {"role": "admin"}).status_code == 403


def test_stored_xss_is_escaped_in_admin_view(client, app):
    payload = "<script>alert(1)</script>"
    client.login("riya")
    client.post("/me/", {"full_name": payload, "email": "a@x.io", "bio": "x"})
    admin = type(client)(app)
    admin.login("admin")
    dash = admin.get("/admin/").data
    assert payload.encode() not in dash
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in dash
