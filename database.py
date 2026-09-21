```python
import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# DATENBANK
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "fundbuero.db"

# Erlaubte Statuswerte.
# Dadurch können keine versehentlichen oder ungültigen
# Statuswerte in der Datenbank gespeichert werden.
STATUS_OPTIONEN = {
    "Verfügbar",
    "Abgeholt",
}


def get_connection():
    """
    Erstellt eine Verbindung zur SQLite-Datenbank.

    Die Row Factory sorgt dafür, dass Datensätze sowohl
    über Spaltennamen als auch über Indexe angesprochen
    werden können.
    """

    connection = sqlite3.connect(str(DATABASE_PATH))

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATENBANK INITIALISIEREN
# ============================================================

def init_database():
    """
    Erstellt die Datenbank und die Tabelle automatisch,
    falls sie noch nicht existieren.
    """

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
                ki_konfidenz REAL,
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
    """
    Speichert ein neues Fundstück.

    Neue Fundstücke werden immer automatisch als
    'Verfügbar' gespeichert.
    """

    if not kategorie:
        raise ValueError("Die Kategorie darf nicht leer sein.")

    # Leere Texte einheitlich als None speichern.
    farbe = farbe.strip() if farbe else None
    groesse = groesse.strip() if groesse else None
    fundort = fundort.strip() if fundort else None
    beschreibung = beschreibung.strip() if beschreibung else None
    bildpfad = str(bildpfad) if bildpfad else None

    # KI-Konfidenz sauber in einen Float umwandeln.
    try:
        ki_konfidenz = float(ki_konfidenz or 0.0)
    except (TypeError, ValueError):
        ki_konfidenz = 0.0

    # Konfidenz auf den gültigen Bereich 0.0–1.0 begrenzen.
    ki_konfidenz = max(0.0, min(1.0, ki_konfidenz))

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
                kategorie.strip(),
                farbe,
                groesse,
                fundort,
                funddatum,
                beschreibung,
                bildpfad,
                ki_konfidenz,
                "Verfügbar",
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
    """
    Gibt alle Fundstücke zurück.

    Neueste Fundstücke stehen zuerst.
    """

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
# EIN FUNDSTÜCK ABRUFEN
# ============================================================

def get_item(item_id):
    """
    Gibt ein einzelnes Fundstück anhand seiner ID zurück.

    Wenn kein passendes Fundstück existiert, wird None
    zurückgegeben.
    """

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
    """
    Sucht nach Fundstücken.

    Unterstützte Filter:
    - Kategorie
    - Farbe
    - Fundort
    - Status
    - Freitext

    Die Freitextsuche durchsucht:
    - Kategorie
    - Farbe
    - Größe
    - Beschreibung
    - Fundort
    """

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

            if status not in STATUS_OPTIONEN:
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

        # ----------------------------------------------------
        # Sortierung
        # ----------------------------------------------------

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
    """
    Ändert den Status eines Fundstücks.

    Erlaubte Werte:
    - Verfügbar
    - Abgeholt
    """

    if status not in STATUS_OPTIONEN:
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
    """
    Löscht ein Fundstück anhand seiner ID.

    Gibt True zurück, wenn tatsächlich ein Datensatz
    gelöscht wurde.
    """

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
    """
    Erstellt Statistiken für das Fundbüro.

    Rückgabe:
        {
            "total": ...,
            "available": ...,
            "collected": ...,
            "bottles": ...,
            "hoodies": ...
        }
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # ----------------------------------------------------
        # Gesamtzahl
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM fundstuecke
            """
        )

        total = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Verfügbare Fundstücke
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM fundstuecke
            WHERE status = 'Verfügbar'
            """
        )

        available = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Abgeholte Fundstücke
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM fundstuecke
            WHERE status = 'Abgeholt'
            """
        )

        collected = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Trinkflaschen
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM fundstuecke
            WHERE kategorie = 'Trinkflasche'
            """
        )

        bottles = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Hoodies
        # ----------------------------------------------------

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
