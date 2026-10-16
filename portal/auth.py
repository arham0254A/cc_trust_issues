from urllib.parse import urlparse

from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from . import throttle

bp = Blueprint("auth", __name__, url_prefix="/auth")

_DUMMY_HASH = generate_password_hash("not-a-real-password")


def _safe_next(target):
    parsed = urlparse(target or "")
    if target and not parsed.scheme and not parsed.netloc and target.startswith("/"):
        return target
    return url_for("events.list_events")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        error = None
        if not (3 <= len(username) <= 32) or not username.replace("_", "").isalnum():
            error = "Username must be 3-32 letters, digits or underscores."
        elif len(password) < 10:
            error = "Password must be at least 10 characters."

        if error is None:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = "That username is taken."
            else:
                flash("Account created. Please log in.")
                return redirect(url_for("auth.login"))
        flash(error)
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        cfg = current_app.config
        user_bucket, ip_bucket = throttle.login_buckets(username, request.remote_addr)

        if throttle.any_locked(user_bucket, ip_bucket):
            flash("Too many attempts. Try again later.")
            return render_template("auth/login.html"), 429

        user = get_db().execute(
            "SELECT id, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()

        valid = check_password_hash(user["password_hash"] if user else _DUMMY_HASH, password)
        if user and valid:
            throttle.reset(user_bucket)
            throttle.reset(ip_bucket)
            session.clear()
            session.permanent = True
            session["user_id"] = user["id"]
            return redirect(_safe_next(request.args.get("next")))

        throttle.record_failure(user_bucket, cfg["LOGIN_MAX_FAILS"], cfg["LOGIN_LOCK_SECONDS"])
        throttle.record_failure(ip_bucket, cfg["LOGIN_IP_MAX_FAILS"], cfg["LOGIN_LOCK_SECONDS"])
        flash("Invalid username or password.")
    return render_template("auth/login.html")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
