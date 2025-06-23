import csv
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path('email_db.sqlite')


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            '''CREATE TABLE IF NOT EXISTS contacts (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   email TEXT NOT NULL UNIQUE,
                   followups_enabled INTEGER DEFAULT 1,
                   step INTEGER DEFAULT 0,
                   last_sent TEXT
               )'''
        )
        c.execute(
            '''CREATE TABLE IF NOT EXISTS log (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   contact_id INTEGER,
                   template TEXT,
                   timestamp TEXT,
                   status TEXT,
                   FOREIGN KEY(contact_id) REFERENCES contacts(id)
               )'''
        )
        conn.commit()


def import_contacts(csv_file):
    with get_conn() as conn, open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('name') or row.get('Name')
            email = row.get('email') or row.get('Email')
            if not name or not email:
                continue
            conn.execute(
                'INSERT OR IGNORE INTO contacts (name, email) VALUES (?, ?)',
                (name.strip(), email.strip())
            )
        conn.commit()


def get_contacts_by_step(step):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('SELECT id, name, email, followups_enabled, step, last_sent FROM contacts WHERE step = ?', (step,))
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def update_contact_step(contact_id, new_step):
    with get_conn() as conn:
        conn.execute('UPDATE contacts SET step = ?, last_sent = ? WHERE id = ?',
                     (new_step, datetime.utcnow().isoformat(), contact_id))
        conn.commit()


def toggle_followups(email, enabled):
    with get_conn() as conn:
        conn.execute('UPDATE contacts SET followups_enabled = ? WHERE email = ?',
                     (1 if enabled else 0, email))
        conn.commit()


def log_email(contact_id, template, status):
    with get_conn() as conn:
        conn.execute('INSERT INTO log (contact_id, template, timestamp, status) VALUES (?, ?, ?, ?)',
                     (contact_id, template, datetime.utcnow().isoformat(), status))
        conn.commit()
