import streamlit as st
from pathlib import Path
from datetime import date, datetime
import uuid

from PIL import Image

from ai_model import (
    predict_image,
    load_labels
)

from database import (
    init_database,
    save_item,
    get_all_items,
    search_items,
    update_item_status,
    delete_item,
    get_statistics
)


# --------------------------------------------------
# STREAMLIT EINSTELLUNGEN
# --------------------------------------------------

st.set_page_config(
    page_title="KathFundBüro",
    page_icon="🔎",
    layout="wide"
)


# --------------------------------------------------
# PROJEKTPFADE
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(
    exist_ok=True
)


# --------------------------------------------------
# DATENBANK STARTEN
# --------------------------------------------------

init_database()


# --------------------------------------------------
# DESIGN
# --------------------------------------------------

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0px;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    margin-bottom: 30px;
    color: gray;
}

.item-card {
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #dddddd;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HILFSFUNKTIONEN
# --------------------------------------------------

def save_uploaded_image(image_file):
    """Speichert ein Bild im uploads-Ordner."""

    try:

        image = Image.open(image_file)

        # Sicherstellen, dass das Bild korrekt ist
        image = image.convert("RGB")

        filename = (
            f"{uuid.uuid4().hex}.jpg"
        )

        file_path = UPLOAD_DIR / filename

        image.save(
            file_path,
            "JPEG"
        )

        return str(file_path)

    except Exception as error:

        raise RuntimeError(
            f"Bild konnte nicht gespeichert werden: {error}"
        )


def show_item_card(item, admin=False):
    """Zeigt eine Fundstück-Karte an."""

    st.markdown(
        '<div class="item-card">',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(
        [1, 2]
    )

    with col1:

        image_path = item["bildpfad"]

        if image_path and Path(image_path).exists():

            try:

                st.image(
                    image_path,
                    width="stretch"
                )

            except Exception:

                st.info(
                    "📷 Bild nicht verfügbar"
                )

        else:

            st.info(
                "📷 Kein Bild vorhanden"
            )

    with col2:

        st.subheader(
            f"🔎 {item['kategorie']}"
        )

        st.write(
            f"**🎨 Farbe:** {item['farbe'] or 'Unbekannt'}"
        )

        st.write(
            f"**📍 Fundort:** {item['fundort'] or 'Unbekannt'}"
        )

        st.write(
            f"**📅 Funddatum:** {item['funddatum']}"
        )

        if item["groesse"]:
            st.write(
                f"**📏 Größe:** {item['groesse']}"
            )

        if item["beschreibung"]:
            st.write(
                f"**📝 Beschreibung:** {item['beschreibung']}"
            )

        if item["status"] == "Verfügbar":

            st.success(
                "🟢 Verfügbar"
            )

        else:

            st.info(
                "✅ Abgeholt"
            )

        # ADMIN-FUNKTIONEN
        if admin:

            st.divider()

            button_col1, button_col2 = st.columns(2)

            with button_col1:

                if item["status"] == "Verfügbar":

                    if st.button(
                        "✅ Als abgeholt markieren",
                        key=f"collect_{item['id']}",
                        width="stretch"
                    ):

                        update_item_status(
                            item["id"],
                            "Abgeholt"
                        )

                        st.rerun()

                else:

                    if st.button(
                        "🟢 Wieder verfügbar machen",
                        key=f"available_{item['id']}",
                        width="stretch"
                    ):

                        update_item_status(
                            item["id"],
                            "Verfügbar"
                        )

                        st.rerun()

            with button_col2:

                if st.button(
                    "🗑️ Löschen",
                    key=f"delete_{item['id']}",
                    width="stretch"
                ):

                    st.session_state[
                        "delete_item_id"
                    ] = item["id"]

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# --------------------------------------------------
# KOPFBEREICH
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🔎 KathFundBüro</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Das digitale Fundbüro des Katharineums'
    '</div>',
    unsafe_allow_html=True
)


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

navigation = st.sidebar.radio(
    "Navigation",
    [
        "📷 Fundstück erfassen",
        "🔍 Fundstücke suchen",
        "📦 Fundbüro verwalten",
        "ℹ️ Informationen"
    ]
)


# ==================================================
# SEITE 1: FUNDSTÜCK ERFASSEN
# ==================================================

if navigation == "📷 Fundstück erfassen":

    st.header(
        "📷 Neues Fundstück erfassen"
    )

    st.write(
        "Lade ein Foto hoch oder fotografiere "
        "einen gefundenen Gegenstand."
    )

    input_type = st.radio(
        "Wie möchtest du ein Bild hinzufügen?",
        [
            "📁 Bild hochladen",
            "📷 Kamera verwenden"
        ]
    )

    image_file = None

    if input_type == "📁 Bild hochladen":

        image_file = st.file_uploader(
            "Bild auswählen",
            type=[
                "jpg",
                "jpeg",
                "png"
            ]
        )

    else:

        image_file = st.camera_input(
            "Foto aufnehmen"
        )

    # Wenn ein Bild vorhanden ist
    if image_file is not None:

        try:

            preview = Image.open(
                image_file
            ).convert("RGB")

            st.image(
                preview,
                caption="Ausgewähltes Bild",
                width="stretch"
            )

        except Exception:

            st.error(
                "⚠️ Das Bild konnte nicht geöffnet werden."
            )

            preview = None

        if preview is not None:

            # KI-Analyse
            if st.button(
                "🤖 Gegenstand mit KI erkennen",
                width="stretch"
            ):

                try:

                    with st.spinner(
                        "🤖 Die KI analysiert den Gegenstand ..."
                    ):

                        # WICHTIG:
                        # Nur ein Argument!
                        result = predict_image(
                            preview
                        )

                    st.session_state[
                        "ai_result"
                    ] = result

                    st.success(
                        "🎉 Gegenstand erfolgreich erkannt!"
                    )

                except Exception as error:

                    st.error(
                        "⚠️ Die KI konnte das Bild "
                        "nicht analysieren."
                    )

                    with st.expander(
                        "Technische Details"
                    ):

                        st.code(
                            str(error)
                        )

            # KI-Ergebnis anzeigen
            if "ai_result" in st.session_state:

                result = st.session_state[
                    "ai_result"
                ]

                st.divider()

                st.subheader(
                    "🧠 KI-Ergebnis"
                )

                confidence_percent = (
                    result["confidence"] * 100
                )

                st.markdown(
                    f"## 🔎 {result['label']}"
                )

                st.metric(
                    "KI-Sicherheit",
                    f"{confidence_percent:.2f} %"
                )

                st.subheader(
                    "📊 Wahrscheinlichkeiten"
                )

                for (
                    label,
                    probability
                ) in result[
                    "probabilities"
                ].items():

                    percentage = (
                        probability * 100
                    )

                    st.write(
                        f"**{label}: "
                        f"{percentage:.2f} %**"
                    )

                    # Werte für Progress Bar begrenzen
                    progress_value = max(
                        0.0,
                        min(
                            float(probability),
                            1.0
                        )
                    )

                    st.progress(
                        progress_value
                    )

                st.divider()

            # Kategorien laden
            try:

                categories = load_labels()

            except Exception:

                categories = [
                    "Kurzehose",
                    "Trinkflasche",
                    "Federtasche",
                    "Hoodie"
                ]

            # Automatische Kategorie
            default_category = categories[0]

            if (
                "ai_result"
                in st.session_state
            ):

                predicted_category = (
                    st.session_state[
                        "ai_result"
                    ]["label"]
                )

                if (
                    predicted_category
                    in categories
                ):

                    default_category = (
                        predicted_category
                    )

            default_index = (
                categories.index(
                    default_category
                )
            )

            # Formular
            st.subheader(
                "💾 Fundstück speichern"
            )

            with st.form(
                "save_item_form"
            ):

                category = st.selectbox(
                    "Kategorie",
                    categories,
                    index=default_index
                )

                color = st.text_input(
                    "Farbe",
                    placeholder="z. B. Blau"
                )

                size = st.selectbox(
                    "Größe",
                    [
                        "Unbekannt",
                        "XS",
                        "S",
                        "M",
                        "L",
                        "XL"
                    ]
                )

                location = st.selectbox(
                    "Fundort",
                    [
                        "Schulhof",
                        "Klassenraum",
                        "Sporthalle",
                        "Mensa",
                        "Flur",
                        "Umkleide",
                        "Sonstiger Ort"
                    ]
                )

                found_date = st.date_input(
                    "Funddatum",
                    value=date.today()
                )

                description = st.text_area(
                    "Zusätzliche Beschreibung",
                    placeholder=(
                        "z. B. Blaue Trinkflasche "
                        "mit schwarzem Deckel."
                    )
                )

                submitted = st.form_submit_button(
                    "💾 Fundstück speichern",
                    width="stretch"
                )

                if submitted:

                    try:

                        # Bild speichern
                        image_file.seek(0)

                        image_path = (
                            save_uploaded_image(
                                image_file
                            )
                        )

                        # KI-Konfidenz
                        confidence = None

                        if (
                            "ai_result"
                            in st.session_state
                        ):

                            confidence = (
                                st.session_state[
                                    "ai_result"
                                ]["confidence"]
                            )

                        # Daten speichern
                        save_item(
                            category,
                            color,
                            size,
                            location,
                            found_date.strftime(
                                "%Y-%m-%d"
                            ),
                            description,
                            image_path,
                            confidence
                        )

                        # KI-Ergebnis zurücksetzen
                        st.session_state.pop(
                            "ai_result",
                            None
                        )

                        st.success(
                            "✅ Das Fundstück wurde "
                            "erfolgreich gespeichert!"
                        )

                    except Exception as error:

                        st.error(
                            "⚠️ Das Fundstück konnte "
                            "nicht gespeichert werden."
                        )

                        st.code(
                            str(error)
                        )


# ==================================================
# SEITE 2: FUNDSTÜCKE SUCHEN
# ==================================================

elif navigation == "🔍 Fundstücke suchen":

    st.header(
        "🔍 Fundstücke suchen"
    )

    st.write(
        "Durchsuche das digitale Fundbüro."
    )

    try:
        categories = load_labels()
    except Exception:
        categories = []

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:

        category_filter = st.selectbox(
            "Kategorie",
            ["Alle"] + categories
        )

        color_filter = st.text_input(
            "Farbe suchen"
        )

    with filter_col2:

        location_filter = st.selectbox(
            "Fundort",
            [
                "Alle",
                "Schulhof",
                "Klassenraum",
                "Sporthalle",
                "Mensa",
                "Flur",
                "Umkleide",
                "Sonstiger Ort"
            ]
        )

        status_filter = st.selectbox(
            "Status",
            [
                "Alle",
                "Verfügbar",
                "Abgeholt"
            ]
        )

    search_text = st.text_input(
        "🔎 Freitextsuche",
        placeholder=(
            "z. B. blaue Trinkflasche"
        )
    )

    results = search_items(
        kategorie=category_filter,
        farbe=color_filter,
        fundort=location_filter,
        status=status_filter,
        suchtext=search_text
    )

    st.divider()

    if not results:

        st.info(
            "🔍 Keine passenden Fundstücke gefunden."
        )

    else:

        st.success(
            f"Es wurden {len(results)} "
            "Fundstücke gefunden."
        )

        for item in results:

            show_item_card(
                item
            )


# ==================================================
# SEITE 3: FUNDBÜRO VERWALTEN
# ==================================================

elif navigation == "📦 Fundbüro verwalten":

    st.header(
        "📦 Fundbüro verwalten"
    )

    statistics = get_statistics()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "📦 Alle Fundstücke",
        statistics["total"]
    )

    col2.metric(
        "🟢 Verfügbar",
        statistics["available"]
    )

    col3.metric(
        "✅ Abgeholt",
        statistics["collected"]
    )

    st.divider()

    st.subheader(
        "Alle gespeicherten Fundstücke"
    )

    items = get_all_items()

    if not items:

        st.info(
            "Noch keine Fundstücke vorhanden. "
            "Füge zuerst ein Fundstück über "
            "„Fundstück erfassen“ hinzu."
        )

    else:

        for item in items:

            show_item_card(
                item,
                admin=True
            )

    # ------------------------------------------------
    # SICHERHEITSABFRAGE FÜR LÖSCHEN
    # ------------------------------------------------

    if (
        "delete_item_id"
        in st.session_state
    ):

        item_id = st.session_state[
            "delete_item_id"
        ]

        st.warning(
            "⚠️ Möchtest du dieses Fundstück "
            "wirklich endgültig löschen?"
        )

        confirm_col1, confirm_col2 = (
            st.columns(2)
        )

        with confirm_col1:

            if st.button(
                "🗑️ Ja, endgültig löschen",
                type="primary",
                width="stretch"
            ):

                delete_item(
                    item_id
                )

                st.session_state.pop(
                    "delete_item_id"
                )

                st.success(
                    "Fundstück wurde gelöscht."
                )

                st.rerun()

        with confirm_col2:

            if st.button(
                "Abbrechen",
                width="stretch"
            ):

                st.session_state.pop(
                    "delete_item_id"
                )

                st.rerun()


# ==================================================
# SEITE 4: INFORMATIONEN
# ==================================================

elif navigation == "ℹ️ Informationen":

    st.header(
        "ℹ️ Über KathFundBüro"
    )

    st.markdown("""
### 🔎 Was ist KathFundBüro?

KathFundBüro ist ein digitales Fundbüro
für das Katharineum.

Die Anwendung hilft dabei, gefundene
Gegenstände zu erfassen, automatisch
zu kategorisieren und später wiederzufinden.

### 🤖 Künstliche Intelligenz

Die App verwendet ein mit
Teachable Machine trainiertes
KI-Modell.

Die KI kann folgende Gegenstände erkennen:

- 🩳 Kurzehose
- 🥤 Trinkflasche
- ✏️ Federtasche
- 👕 Hoodie

### ⚠️ Wichtig

Die künstliche Intelligenz unterstützt
bei der Erkennung, kann aber Fehler machen.

Deshalb kann die Kategorie vor dem
Speichern immer manuell geändert werden.

### 💾 Datenschutz

Diese Version ist ein Schulprojekt.

Die Fundstücke werden lokal in einer
SQLite-Datenbank gespeichert.
""")
