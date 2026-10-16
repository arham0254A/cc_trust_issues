"""Bonus: account lockout and per-IP rate limiting on login."""


def test_account_locks_after_threshold(client):
    for _ in range(3):
        r = client.login("riya", "wrong")
        assert b"Invalid username or password" in r.data
    r = client.login("riya", "wrong")
    assert r.status_code == 429
    assert b"Too many attempts" in r.data
    r = client.login("riya", "correct-horse")
    assert r.status_code == 429


def test_successful_login_resets_the_counter(client):
    client.login("riya", "wrong")
    client.login("riya", "wrong")
    assert client.login("riya").status_code == 302
    client.c.get("/auth/logout")
    for _ in range(3):
        client.login("riya", "wrong")
    assert client.login("riya", "wrong").status_code == 429


def test_lockout_is_per_account_not_global(client, app):
    for _ in range(3):
        client.login("riya", "wrong")
    assert client.login("riya", "wrong").status_code == 429
    aditya = type(client)(app)
    assert aditya.login("aditya").status_code == 302
