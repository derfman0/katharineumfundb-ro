import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fundbuero.db"

def _connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_database():
    with _connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS fundstuecke (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategorie TEXT NOT NULL,
            farbe TEXT,
            groesse TEXT,
            fundort TEXT,
            funddatum TEXT NOT NULL,
            beschreibung TEXT,
            bildpfad TEXT,
            ki_konfidenz REAL,
            status TEXT NOT NULL DEFAULT 'Verfügbar',
            erstellt_am TEXT NOT NULL
        )""")

def save_item(kategorie, farbe, groesse, fundort, funddatum,
              beschreibung, bildpfad, ki_konfidenz, status="Verfügbar"):
    with _connect() as con:
        cur = con.execute("""
        INSERT INTO fundstuecke
        (kategorie, farbe, groesse, fundort, funddatum, beschreibung,
         bildpfad, ki_konfidenz, status, erstellt_am)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (kategorie, farbe, groesse, fundort, str(funddatum), beschreibung,
         bildpfad, float(ki_konfidenz), status,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        return cur.lastrowid

def get_all_items():
    with _connect() as con:
        rows = con.execute("SELECT * FROM fundstuecke ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]

def search_items(kategorie=None, farbe=None, fundort=None,
                 funddatum=None, freitext=None, status=None):
    query = "SELECT * FROM fundstuecke WHERE 1=1"
    params = []
    if kategorie and kategorie != "Alle":
        query += " AND kategorie = ?"; params.append(kategorie)
    if farbe:
        query += " AND LOWER(farbe) LIKE ?"; params.append(f"%{farbe.lower()}%")
    if fundort and fundort != "Alle":
        query += " AND fundort = ?"; params.append(fundort)
    if funddatum:
        query += " AND funddatum = ?"; params.append(str(funddatum))
    if freitext:
        value = f"%{freitext.lower()}%"
        query += " AND (LOWER(kategorie) LIKE ? OR LOWER(farbe) LIKE ? OR LOWER(fundort) LIKE ? OR LOWER(beschreibung) LIKE ?)"
        params.extend([value, value, value, value])
    if status and status != "Alle":
        query += " AND status = ?"; params.append(status)
    query += " ORDER BY id DESC"
    with _connect() as con:
        rows = con.execute(query, params).fetchall()
    return [dict(row) for row in rows]

def update_item_status(item_id, status):
    if status not in ("Verfügbar", "Abgeholt"):
        raise ValueError("Ungültiger Status")
    with _connect() as con:
        con.execute("UPDATE fundstuecke SET status = ? WHERE id = ?",
                    (status, int(item_id)))

def delete_item(item_id):
    with _connect() as con:
        row = con.execute("SELECT * FROM fundstuecke WHERE id = ?",
                          (int(item_id),)).fetchone()
        if row is None:
            return None
        con.execute("DELETE FROM fundstuecke WHERE id = ?", (int(item_id),))
        return dict(row)

def get_statistics():
    with _connect() as con:
        count = lambda q, p=(): con.execute(q, p).fetchone()[0]
        return {
            "gesamt": count("SELECT COUNT(*) FROM fundstuecke"),
            "verfuegbar": count("SELECT COUNT(*) FROM fundstuecke WHERE status='Verfügbar'"),
            "abgeholt": count("SELECT COUNT(*) FROM fundstuecke WHERE status='Abgeholt'"),
            "trinkflaschen": count("SELECT COUNT(*) FROM fundstuecke WHERE kategorie='Trinkflasche'"),
            "hoodies": count("SELECT COUNT(*) FROM fundstuecke WHERE kategorie='Hoodie'")
        }
