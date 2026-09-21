```python
import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# DATENBANK
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "fundbuero.db"


def get_connection():
    """Erstellt eine Verbindung zur SQLite-Datenbank."""

    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATENBANK INITIALISIEREN
# ============================================================

def init_database():
    """Erstellt die Datenbank und Tabelle automatisch."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fundstuecke (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kategorie TEXT NOT NULL,
                farbe TEXT,
                groesse TEXT,
                fundort TEXT,
                funddatum TEXT,
                beschreibung TEXT,
                bildpfad TEXT,
                ki_konfidenz REAL DEFAULT 0,
                status TEXT DEFAULT 'Verfügbar',
                erstellt_am TEXT
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# FUNDSTÜCK SPEICHERN
# ============================================================

def save_item(
    kategorie,
    farbe,
    groesse,
    fundort,
    funddatum,
    beschreibung,
    bildpfad,
    ki_konfidenz=0.0,
):
    """Speichert ein neues Fundstück."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO fundstuecke (
                kategorie,
                farbe,
                groesse,
                fundort,
                funddatum,
                beschreibung,
                bildpfad,
                ki_konfidenz,
                status,
                erstellt_am
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                kategorie,
                farbe,
                groesse,
                fundort,
                funddatum,
                beschreibung,
                bildpfad,
                float(ki_konfidenz or 0),
                "Verfügbar",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# ALLE FUNDSTÜCKE
# ============================================================

def get_all_items():
    """Gibt alle Fundstücke zurück."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM fundstuecke
            ORDER BY id DESC
            """
        )

        return cursor.fetchall()

    finally:
        connection.close()


# ============================================================
# FUNDSTÜCKE SUCHEN
# ============================================================

def search_items(
    kategorie=None,
    farbe=None,
    fundort=None,
    status=None,
    suchtext=None,
):
    """Sucht nach Fundstücken."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            SELECT *
            FROM fundstuecke
            WHERE 1=1
        """

        parameters = []

        # ----------------------------------------------------
        # Kategorie
        # ----------------------------------------------------

        if kategorie and kategorie != "Alle":
            query += """
                AND kategorie = ?
            """
            parameters.append(kategorie)

        # ----------------------------------------------------
        # Farbe
        # ----------------------------------------------------

        if farbe:
            query += """
                AND LOWER(COALESCE(farbe, '')) LIKE LOWER(?)
            """
            parameters.append(f"%{farbe}%")

        # ----------------------------------------------------
        # Fundort
        # ----------------------------------------------------

        if fundort and fundort != "Alle":
            query += """
                AND fundort = ?
            """
            parameters.append(fundort)

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        if status and status != "Alle":
            query += """
                AND status = ?
            """
            parameters.append(status)

        # ----------------------------------------------------
        # Freitextsuche
        # ----------------------------------------------------

        if suchtext:
            query += """
                AND (
                    LOWER(COALESCE(kategorie, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(farbe, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(groesse, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(beschreibung, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(fundort, '')) LIKE LOWER(?)
                )
            """

            text = f"%{suchtext}%"

            parameters.extend(
                [
                    text,
                    text,
                    text,
                    text,
                    text,
                ]
            )

        query += """
            ORDER BY id DESC
        """

        cursor.execute(query, parameters)

        return cursor.fetchall()

    finally:
        connection.close()


# ============================================================
# STATUS ÄNDERN
# ============================================================

def update_item_status(item_id, status):
    """Ändert den Status eines Fundstücks."""

    erlaubte_status = {
        "Verfügbar",
        "Abgeholt",
    }

    if status not in erlaubte_status:
        raise ValueError("Ungültiger Status.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE fundstuecke
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                item_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# FUNDSTÜCK LÖSCHEN
# ============================================================

def delete_item(item_id):
    """Löscht ein Fundstück aus der Datenbank."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM fundstuecke
            WHERE id = ?
            """,
            (item_id,),
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# STATISTIK
# ============================================================

def get_statistics():
    """Erstellt Statistiken für das Fundbüro."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Gesamtzahl
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM fundstuecke
            """
        )

        total = cursor.fetchone()[0]

        # Verfügbar
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM fundstuecke
            WHERE status = 'Verfügbar'
            """
        )

        available = cursor.fetchone()[0]

        # Abgeholt
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM fundstuecke
            WHERE status = 'Abgeholt'
            """
        )

        collected = cursor.fetchone()[0]

        # Trinkflaschen
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM fundstuecke
            WHERE kategorie = 'Trinkflasche'
            """
        )

        bottles = cursor.fetchone()[0]

        # Hoodies
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM fundstuecke
            WHERE kategorie = 'Hoodie'
            """
        )

        hoodies = cursor.fetchone()[0]

        return {
            "total": total,
            "available": available,
            "collected": collected,
            "bottles": bottles,
            "hoodies": hoodies,
        }

    finally:
        connection.close()
```
