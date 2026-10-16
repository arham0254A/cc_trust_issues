import sqlite3

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
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
    init_db()
    seed()
    click.echo("Initialized the VULNERABLE database with seed data.")


def seed():
    # WEAKNESS
    db = get_db()
    db.executescript(
        """
        INSERT INTO users (username, password_hash, role, full_name, email) VALUES
          ('admin', 'SuperSecretAdmin1', 'admin',  'Club Admin',  'admin@club.test'),
          ('riya', 'riyapassword',     'member', 'Riya Member','riya@club.test'),
          ('aditya',   'adityapassword',       'member', 'Aditya Member',  'aditya@club.test');
        INSERT INTO events (title, description, starts_at, capacity, created_by) VALUES
          ('Hackathon', 'Annual all-night hack.', '2026-11-01T10:00', 50, 1);
        """
    )
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
