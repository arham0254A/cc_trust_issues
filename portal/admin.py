from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .db import get_db
from .members import login_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


# VULN #4
@bp.route("/")
@login_required
def dashboard():
    db = get_db()
    users = db.execute(
        "SELECT id, username, role, full_name, email, created_at FROM users ORDER BY id"
    ).fetchall()
    events = db.execute(
        "SELECT e.id, e.title, e.starts_at, e.capacity,"
        " (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id) AS taken"
        " FROM events e ORDER BY e.starts_at"
    ).fetchall()
    return render_template("admin/dashboard.html", users=users, events=events)


@bp.route("/events/<int:event_id>/attendees")
@login_required
def attendees(event_id):
    db = get_db()
    event = db.execute("SELECT id, title FROM events WHERE id = ?", (event_id,)).fetchone()
    people = db.execute(
        "SELECT u.username, u.full_name, u.email, r.created_at FROM registrations r"
        " JOIN users u ON u.id = r.user_id WHERE r.event_id = ?",
        (event_id,),
    ).fetchall()
    return render_template("admin/attendees.html", event=event, people=people)


@bp.route("/events/new", methods=("GET", "POST"))
@login_required
def create_event():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        starts_at = request.form.get("starts_at", "")
        capacity = request.form.get("capacity", "0")
        db = get_db()
        db.execute(
            "INSERT INTO events (title, description, starts_at, capacity, created_by)"
            " VALUES (?, ?, ?, ?, ?)",
            (title, description, starts_at or datetime.now().isoformat(), int(capacity or 1), g.user["id"]),
        )
        db.commit()
        flash("Event created.")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/new_event.html")


@bp.route("/users/<int:user_id>/role", methods=("POST",))
@login_required
def set_role(user_id):
    db = get_db()
    db.execute("UPDATE users SET role = ? WHERE id = ?", (request.form.get("role"), user_id))
    db.commit()
    flash("Role updated.")
    return redirect(url_for("admin.dashboard"))
