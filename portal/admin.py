from datetime import datetime

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .db import get_db
from .security import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@role_required("admin")
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
@role_required("admin")
def attendees(event_id):
    db = get_db()
    event = db.execute("SELECT id, title FROM events WHERE id = ?", (event_id,)).fetchone()
    if event is None:
        abort(404)
    people = db.execute(
        "SELECT u.username, u.full_name, u.email, r.created_at FROM registrations r"
        " JOIN users u ON u.id = r.user_id WHERE r.event_id = ? ORDER BY r.created_at",
        (event_id,),
    ).fetchall()
    return render_template("admin/attendees.html", event=event, people=people)


@bp.route("/events/new", methods=("GET", "POST"))
@role_required("admin")
def create_event():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        starts_at = request.form.get("starts_at", "")
        try:
            capacity = int(request.form.get("capacity", ""))
            datetime.fromisoformat(starts_at)
        except ValueError:
            capacity = None
        if not (1 <= len(title) <= 120) or capacity is None or not (1 <= capacity <= 10000):
            flash("Need a title, a valid start time and a capacity between 1 and 10000.")
        else:
            db = get_db()
            db.execute(
                "INSERT INTO events (title, description, starts_at, capacity, created_by)"
                " VALUES (?, ?, ?, ?, ?)",
                (title, description[:2000], starts_at, capacity, g.user["id"]),
            )
            db.commit()
            flash("Event created.")
            return redirect(url_for("admin.dashboard"))
    return render_template("admin/new_event.html")


@bp.route("/users/<int:user_id>/role", methods=("POST",))
@role_required("admin")
def set_role(user_id):
    role = request.form.get("role")
    if role not in ("member", "admin"):
        abort(400)
    if user_id == g.user["id"]:
        flash("You can't change your own role.")
        return redirect(url_for("admin.dashboard"))
    db = get_db()
    db.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    db.commit()
    flash("Role updated.")
    return redirect(url_for("admin.dashboard"))
