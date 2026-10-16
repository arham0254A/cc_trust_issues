from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        # VULN #2
        role = request.form.get("role", "member")
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password, role),
            )
            db.commit()
        except db.IntegrityError:
            flash("That username is taken.")
        else:
            flash("Account created. Please log in.")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # VULN #1
        query = (
            "SELECT * FROM users WHERE username = '%s' AND password_hash = '%s'"
            % (username, password)
        )
        user = get_db().execute(query).fetchone()
        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("events.list_events"))
        flash("Invalid username or password.")
    return render_template("auth/login.html")


@bp.route("/logout", methods=("GET", "POST"))
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
