import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# DATENBANK
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "fundbuero.db"

STATUS_VERFUEGBAR = "Verfügbar"
STATUS_ABGEHOLT = "Abgeholt"

GUELTIGE_STATUS = {
    STATUS_VERFUEGBAR,
    STATUS_ABGEHOLT,
}


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
    ki_konfidenz,
):
    """Speichert ein neues Fundstück."""

    if not kategorie:
        raise ValueError("Die Kategorie darf nicht leer sein.")

    try:
        confidence = float(ki_konfidenz or 0)
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(0.0, min(1.0, confidence))

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
                str(kategorie).strip(),
                str(farbe).strip() if farbe else None,
                str(groesse).strip() if groesse else None,
                str(fundort).strip() if fundort else None,
                str(funddatum) if funddatum else None,
                str(beschreibung).strip() if beschreibung else None,
                str(bildpfad) if bildpfad else None,
                confidence,
                STATUS_VERFUEGBAR,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        connection.commit()

        return cursor.lastrowid

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
# EIN FUNDSTÜCK
# ============================================================

def get_item(item_id):
    """Gibt ein einzelnes Fundstück zurück."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM fundstuecke
            WHERE id = ?
            """,
            (item_id,),
        )

        return cursor.fetchone()

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
            WHERE 1 = 1
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

        if farbe and farbe.strip():
            query += """
                AND LOWER(COALESCE(farbe, '')) LIKE LOWER(?)
            """

            parameters.append(f"%{farbe.strip()}%")

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

            if status not in GUELTIGE_STATUS:
                raise ValueError(
                    f"Ungültiger Status: {status}"
                )

            query += """
                AND status = ?
            """

            parameters.append(status)

        # ----------------------------------------------------
        # Freitext
        # ----------------------------------------------------

        if suchtext and suchtext.strip():

            text = f"%{suchtext.strip()}%"

            query += """
                AND (
                    LOWER(COALESCE(kategorie, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(farbe, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(groesse, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(beschreibung, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(fundort, '')) LIKE LOWER(?)
                )
            """

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

    if status not in GUELTIGE_STATUS:
        raise ValueError(
            f"Ungültiger Status: {status}"
        )

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

        return cursor.rowcount > 0

    finally:
        connection.close()


# ============================================================
# FUNDSTÜCK LÖSCHEN
# ============================================================

def delete_item(item_id):
    """Löscht ein Fundstück."""

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

        return cursor.rowcount > 0

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

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE
                        WHEN status = 'Verfügbar'
                        THEN 1
                        ELSE 0
                    END
                ) AS available,
                SUM(
                    CASE
                        WHEN status = 'Abgeholt'
                        THEN 1
                        ELSE 0
                    END
                ) AS collected,
                SUM(
                    CASE
                        WHEN kategorie = 'Trinkflasche'
                        THEN 1
                        ELSE 0
                    END
                ) AS bottles,
                SUM(
                    CASE
                        WHEN kategorie = 'Hoodie'
                        THEN 1
                        ELSE 0
                    END
                ) AS hoodies
            FROM fundstuecke
            """
        )

        row = cursor.fetchone()

        return {
            "total": row["total"] or 0,
            "available": row["available"] or 0,
            "collected": row["collected"] or 0,
            "bottles": row["bottles"] or 0,
            "hoodies": row["hoodies"] or 0,
        }

    finally:
        connection.close()
