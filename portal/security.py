import functools
import secrets

from flask import abort, g, redirect, request, session, url_for


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)
    return wrapped


def role_required(*roles):
    """Allow the view only for users whose role (read from the DB, not the client) is in `roles`."""
    def decorator(view):
        @functools.wraps(view)
        @login_required
        def wrapped(**kwargs):
            if g.user["role"] not in roles:
                abort(403)
            return view(**kwargs)
        return wrapped
    return decorator


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def check_csrf():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token")
        if not expected or not secrets.compare_digest(sent, expected):
            abort(400, "Invalid CSRF token")


def set_security_headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response
