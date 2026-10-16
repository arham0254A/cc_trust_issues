import sqlite3

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))


@click.command("init-db")
def init_db_command():
    """Drop and recreate all tables."""
    init_db()
    click.echo("Initialized the database.")


@click.command("create-admin")
@click.argument("username")
@click.password_option()
def create_admin_command(username, password):
    """Create an admin account. Admins are never created through the web UI."""
    db = get_db()
    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
        (username, generate_password_hash(password)),
    )
    db.commit()
    click.echo(f"Created admin '{username}'.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
