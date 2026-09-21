import base64
from datetime import date
from pathlib import Path
from uuid import uuid4

import streamlit as st

from database import (
    init_database,
    save_item,
    search_items,
    update_item_status,
    delete_item,
    get_statistics,
)

from ai_model import predict_image, CATEGORIES


# ============================================================
# KONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Kath. FundBüro",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# VERZEICHNISSE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# DATENBANK
# ============================================================

init_database()


# ============================================================
# KONSTANTEN
# ============================================================

FUNDORTE = [
    "Aula",
    "Bibliothek",
    "Sporthalle",
    "Pausenhof",
    "Klassenraum",
    "Flur",
    "Treppenhaus",
    "Mensa",
    "Schulhof",
    "Sonstiger Ort",
]

FUNDORTE_FILTER = ["Alle"] + FUNDORTE

STATUS_OPTIONEN = [
    "Alle",
    "Verfügbar",
    "Abgeholt",
]


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "page": "Startseite",
    "uploaded_image": None,
    "image_path": None,
    "ai_result": None,
    "ai_top_results": [],
    "processed_file_id": None,
    "form_reset": 0,
}


for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# DESIGN
# ============================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    .stApp {
        background: #f6f7f8;
    }

    html,
    body,
    [class*="css"] {
        font-family: "Inter", sans-serif;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: #171717;
    }

    .brand {
        padding: 18px 0 24px 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 30px;
    }

    .brand-name {
        font-size: 24px;
        font-weight: 800;
        color: #171717;
    }

    .brand-subtitle {
        font-size: 12px;
        color: #6b7280;
        margin-top: 3px;
    }

    .hero {
        background: linear-gradient(
            135deg,
            #ffffff 0%,
            #ffffff 60%,
            #fff1f3 100%
        );

        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 48px;
        margin-bottom: 30px;
    }

    .hero-accent {
        width: 60px;
        height: 5px;
        background: #c8102e;
        border-radius: 10px;
        margin-bottom: 20px;
    }

    .hero-small {
        color: #c8102e;
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .08em;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: 46px;
        font-weight: 800;
        letter-spacing: -2px;
        color: #171717;
        margin-bottom: 15px;
    }

    .hero-text {
        max-width: 650px;
        color: #6b7280;
        font-size: 16px;
        line-height: 1.7;
    }

    .card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 25px;
        min-height: 190px;
        box-shadow: 0 4px 18px rgba(0,0,0,.04);
    }

    .card-icon {
        font-size: 28px;
        margin-bottom: 14px;
    }

    .card-title {
        font-size: 18px;
        font-weight: 700;
        color: #171717;
        margin-bottom: 8px;
    }

    .card-text {
        color: #6b7280;
        font-size: 13px;
        line-height: 1.6;
    }

    .stat {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 22px;
    }

    .stat-label {
        color: #6b7280;
        font-size: 12px;
        font-weight: 600;
    }

    .stat-number {
        color: #171717;
        font-size: 32px;
        font-weight: 800;
        margin-top: 6px;
    }

    .stat-text {
        color: #9ca3af;
        font-size: 11px;
        margin-top: 3px;
    }

    .section-title {
        color: #171717;
        font-size: 22px;
        font-weight: 800;
        margin-top: 35px;
        margin-bottom: 16px;
    }

    .info {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 24px;
    }

    .info-title {
        font-size: 17px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .info-text {
        color: #6b7280;
        line-height: 1.7;
        font-size: 13px;
    }

    .ai-box {
        background: #fff5f7;
        border: 1px solid #f1c5cc;
        border-radius: 16px;
        padding: 22px;
    }

    .ai-label {
        color: #c8102e;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .08em;
    }

    .ai-result {
        color: #171717;
        font-size: 23px;
        font-weight: 800;
        margin-top: 7px;
    }

    .item-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 15px;
    }

    .item-content {
        padding: 16px;
    }

    .item-title {
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 7px;
    }

    .item-meta {
        color: #6b7280;
        font-size: 12px;
        line-height: 1.8;
    }

    .status {
        display: inline-block;
        margin-top: 10px;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 700;
    }

    .available {
        background: #e9f8ef;
        color: #16803c;
    }

    .collected {
        background: #edf4ff;
        color: #2563eb;
    }

    .stButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def go_to(page):
    st.session_state.page = page
    st.rerun()


def reset_upload():
    st.session_state.uploaded_image = None
    st.session_state.image_path = None
    st.session_state.ai_result = None
    st.session_state.ai_top_results = []
    st.session_state.processed_file_id = None
    st.session_state.form_reset += 1


def normalize_results(results):
    normalized = []

    if not results:
        return normalized

    for result in results:

        if isinstance(result, dict):
            label = result.get("label", "")
            score = result.get("score", 0)

        elif isinstance(result, (tuple, list)) and len(result) >= 2:
            label = result[0]
            score = result[1]

        else:
            continue

        try:
            score = float(score)
        except Exception:
            score = 0.0

        normalized.append(
            {
                "label": str(label),
                "score": score,
            }
        )

    return normalized


def image_data_uri(path):
    if not path:
        return None

    try:
        path = Path(path)

        if not path.exists():
            return None

        suffix = path.suffix.lower()

        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }

        mime = mime_types.get(suffix, "image/jpeg")

        data = base64.b64encode(
            path.read_bytes()
        ).decode("utf-8")

        return f"data:{mime};base64,{data}"

    except Exception:
        return None


# ============================================================
# NAVIGATION
# ============================================================

def render_navigation():

    st.markdown(
        """
        <div class="brand">
            <div class="brand-name">
                🔴 Kath. FundBüro
            </div>

            <div class="brand-subtitle">
                Digitales Fundbüro · Katharineum
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button(
            "Startseite",
            use_container_width=True,
            key="nav_home",
        ):
            go_to("Startseite")

    with col2:
        if st.button(
            "Suchen",
            use_container_width=True,
            key="nav_search",
        ):
            go_to("Fundstücke suchen")

    with col3:
        if st.button(
            "Erfassen",
            use_container_width=True,
            key="nav_add",
        ):
            go_to("Fundstück erfassen")

    with col4:
        if st.button(
            "Verwaltung",
            use_container_width=True,
            key="nav_admin",
        ):
            go_to("Fundbüro verwalten")

    with col5:
        if st.button(
            "Informationen",
            use_container_width=True,
            key="nav_info",
        ):
            go_to("Informationen")

    st.write("")


# ============================================================
# STARTSEITE
# ============================================================

def render_home():

    st.markdown(
        """
        <div class="hero">

            <div class="hero-accent"></div>

            <div class="hero-small">
                Willkommen im digitalen Fundbüro
            </div>

            <div class="hero-title">
                Kath. FundBüro
            </div>

            <div class="hero-text">
                Verlorene Gegenstände finden, Fundstücke melden
                und alles rund um das Fundbüro des Katharineums
                einfach verwalten.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">Was möchtest du machen?</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="card">
                <div class="card-icon">➕</div>
                <div class="card-title">
                    Fundstück erfassen
                </div>
                <div class="card-text">
                    Fotografiere einen gefundenen Gegenstand.
                    Die KI unterstützt dich bei der Erkennung.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Fundstück erfassen",
            use_container_width=True,
            key="home_add",
        ):
            go_to("Fundstück erfassen")

    with c2:
        st.markdown(
            """
            <div class="card">
                <div class="card-icon">🔎</div>
                <div class="card-title">
                    Fundstücke suchen
                </div>
                <div class="card-text">
                    Durchsuche das Fundbüro nach Kategorie,
                    Fundort, Farbe oder Suchbegriff.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Fundstücke suchen",
            use_container_width=True,
            key="home_search",
        ):
            go_to("Fundstücke suchen")

    with c3:
        st.markdown(
            """
            <div class="card">
                <div class="card-icon">📋</div>
                <div class="card-title">
                    Fundbüro verwalten
                </div>
                <div class="card-text">
                    Fundstücke verwalten, Status ändern
                    und den Überblick behalten.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Verwaltungsbereich",
            use_container_width=True,
            key="home_admin",
        ):
            go_to("Fundbüro verwalten")

    stats = get_statistics()

    st.markdown(
        '<div class="section-title">Aktueller Überblick</div>',
        unsafe_allow_html=True,
    )

    s1, s2, s3 = st.columns(3)

    with s1:
        st.markdown(
            f"""
            <div class="stat">
                <div class="stat-label">
                    Gesamte Fundstücke
                </div>

                <div class="stat-number">
                    {stats["total"]}
                </div>

                <div class="stat-text">
                    gespeicherte Fundstücke
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            f"""
            <div class="stat">
                <div class="stat-label">
                    Verfügbar
                </div>

                <div class="stat-number">
                    {stats["available"]}
                </div>

                <div class="stat-text">
                    aktuell im Fundbüro
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s3:
        st.markdown(
            f"""
            <div class="stat">
                <div class="stat-label">
                    Abgeholt
                </div>

                <div class="stat-number">
                    {stats["collected"]}
                </div>

                <div class="stat-text">
                    bereits zurückgegeben
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# FUNDSTÜCK ERFASSEN
# ============================================================

def render_add_item():

    st.title("Fundstück erfassen")

    st.write(
        "Lade ein Foto hoch, lass die KI den Gegenstand "
        "erkennen und ergänze anschließend die Angaben."
    )

    st.subheader("1. Foto")

    reset_suffix = st.session_state.form_reset

    uploaded_file = st.file_uploader(
        "Foto auswählen",
        type=["jpg", "jpeg", "png", "webp"],
        key=f"upload_{reset_suffix}",
    )

    camera_file = st.camera_input(
        "Oder direkt mit der Kamera aufnehmen",
        key=f"camera_{reset_suffix}",
    )

    selected_file = camera_file or uploaded_file

    if selected_file is not None:

        file_id = getattr(
            selected_file,
            "file_id",
            None,
        )

        if file_id is None:
            file_id = (
                f"{selected_file.name}_"
                f"{len(selected_file.getvalue())}"
            )

        if file_id != st.session_state.processed_file_id:

            image_bytes = selected_file.getvalue()

            suffix = Path(
                selected_file.name
            ).suffix.lower()

            if suffix not in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            ]:
                suffix = ".jpg"

            filename = (
                f"{uuid4().hex}{suffix}"
            )

            image_path = UPLOAD_DIR / filename

            image_path.write_bytes(image_bytes)

            st.session_state.uploaded_image = image_bytes
            st.session_state.image_path = str(image_path)
            st.session_state.processed_file_id = file_id

            st.session_state.ai_result = None
            st.session_state.ai_top_results = []

        st.image(
            st.session_state.uploaded_image,
            caption="Ausgewähltes Foto",
            use_container_width=True,
        )

        if st.button(
            "KI-Erkennung starten",
            type="primary",
            use_container_width=True,
            key="run_ai",
        ):

            try:

                with st.spinner(
                    "Die KI analysiert das Fundstück ..."
                ):

                    label, confidence, top_results = predict_image(
                        selected_file
                    )

                st.session_state.ai_result = (
                    label,
                    float(confidence),
                )

                st.session_state.ai_top_results = (
                    normalize_results(top_results)
                )

                st.success(
                    "KI-Erkennung abgeschlossen."
                )

            except Exception as error:

                st.error(
                    "Die KI-Erkennung konnte nicht "
                    f"durchgeführt werden: {error}"
                )

    st.subheader("2. Angaben")

    left, right = st.columns(2)

    with left:

        detected_category = "Sonstiger Gegenstand"

        if st.session_state.ai_result:
            detected_category = (
                st.session_state.ai_result[0]
            )

        category_options = list(CATEGORIES)

        if (
            detected_category
            not in category_options
        ):
            detected_category = (
                "Sonstiger Gegenstand"
            )

        if detected_category not in category_options:
            category_options.append(
                detected_category
            )

        category_index = category_options.index(
            detected_category
        )

        kategorie = st.selectbox(
            "Kategorie",
            category_options,
            index=category_index,
        )

        farbe = st.text_input(
            "Farbe",
            placeholder="z. B. blau, schwarz, rot",
        )

        groesse = st.text_input(
            "Größe",
            placeholder="z. B. M, 42, klein",
        )

    with right:

        fundort = st.selectbox(
            "Fundort",
            FUNDORTE,
        )

        funddatum = st.date_input(
            "Funddatum",
            value=date.today(),
            format="DD.MM.YYYY",
        )

        beschreibung = st.text_area(
            "Weitere Beschreibung",
            placeholder=(
                "Besondere Merkmale, Aufdrucke, "
                "Beschädigungen oder andere Hinweise ..."
            ),
            height=120,
        )

    if st.session_state.ai_result:

        label, confidence = (
            st.session_state.ai_result
        )

        st.markdown(
            f"""
            <div class="ai-box">

                <div class="ai-label">
                    KI-Erkennung
                </div>

                <div class="ai-result">
                    {label}
                </div>

                <div style="color:#6b7280; margin-top:5px;">
                    Erkennungswahrscheinlichkeit:
                    <strong>
                        {confidence * 100:.0f}%
                    </strong>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        top_results = (
            st.session_state.ai_top_results
        )

        if top_results:

            st.write("Weitere Möglichkeiten:")

            for result in top_results[:4]:

                st.write(
                    f'{result["label"]} — '
                    f'{result["score"] * 100:.0f}%'
                )

    st.write("")

    if st.button(
        "Fundstück speichern",
        type="primary",
        use_container_width=True,
        key="save_item",
    ):

        if st.session_state.image_path is None:

            st.warning(
                "Bitte lade zuerst ein Foto hoch."
            )

        elif not kategorie:

            st.warning(
                "Bitte wähle eine Kategorie."
            )

        else:

            try:

                confidence = 0.0

                if st.session_state.ai_result:
                    confidence = float(
                        st.session_state.ai_result[1]
                    )

                save_item(
                    kategorie=kategorie,
                    farbe=farbe,
                    groesse=groesse,
                    fundort=fundort,
                    funddatum=funddatum.strftime(
                        "%Y-%m-%d"
                    ),
                    beschreibung=beschreibung,
                    bildpfad=st.session_state.image_path,
                    ki_konfidenz=confidence,
                )

                st.success(
                    "Das Fundstück wurde erfolgreich gespeichert."
                )

                reset_upload()

                st.rerun()

            except Exception as error:

                st.error(
                    "Beim Speichern ist ein Fehler "
                    f"aufgetreten: {error}"
                )


# ============================================================
# SUCHEN
# ============================================================

def render_search():

    st.title("Fundstücke suchen")

    st.write(
        "Durchsuche das Fundbüro nach verlorenen "
        "und gefundenen Gegenständen."
    )

    search_text = st.text_input(
        "Suchbegriff",
        placeholder=(
            "z. B. Rucksack, blau, Sporthalle ..."
        ),
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        category = st.selectbox(
            "Kategorie",
            ["Alle"] + list(CATEGORIES),
        )

    with c2:
        location = st.selectbox(
            "Fundort",
            FUNDORTE_FILTER,
        )

    with c3:
        status = st.selectbox(
            "Status",
            STATUS_OPTIONEN,
        )

    results = search_items(
        kategorie=category,
        fundort=location,
        status=status,
        suchtext=search_text,
    )

    st.subheader(
        f"{len(results)} Fundstück(e) gefunden"
    )

    if not results:

        st.info(
            "Keine passenden Fundstücke gefunden."
        )

        return

    for start in range(
        0,
        len(results),
        4,
    ):

        row = results[
            start:start + 4
        ]

        columns = st.columns(
            len(row)
        )

        for column, item in zip(
            columns,
            row,
        ):

            with column:

                st.markdown(
                    '<div class="item-card">',
                    unsafe_allow_html=True,
                )

                if item.get("bildpfad"):

                    image = image_data_uri(
                        item["bildpfad"]
                    )

                    if image:

                        st.image(
                            image,
                            use_container_width=True,
                        )

                st.markdown(
                    f"""
                    <div class="item-content">

                        <div class="item-title">
                            {item["kategorie"]}
                        </div>

                        <div class="item-meta">
                            Fundort:
                            {item["fundort"]}
                            <br>
                            Datum:
                            {item["funddatum"]}
                            <br>
                            Farbe:
                            {item.get("farbe") or "-"}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if item["status"] == "Verfügbar":

                    st.success(
                        "● Verfügbar"
                    )

                else:

                    st.info(
                        "● Abgeholt"
                    )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True,
                )


# ============================================================
# VERWALTUNG
# ============================================================

def render_admin():

    st.title("Fundbüro verwalten")

    stats = get_statistics()

    a, b, c, d = st.columns(4)

    with a:
        st.metric(
            "Gesamt",
            stats["total"],
        )

    with b:
        st.metric(
            "Verfügbar",
            stats["available"],
        )

    with c:
        st.metric(
            "Abgeholt",
            stats["collected"],
        )

    with d:
        st.metric(
            "Trinkflaschen",
            stats["bottles"],
        )

    st.subheader("Alle Fundstücke")

    search = st.text_input(
        "Suche",
        placeholder=(
            "Kategorie, Farbe, Beschreibung oder Fundort ..."
        ),
    )

    status = st.selectbox(
        "Status",
        STATUS_OPTIONEN,
        key="admin_status",
    )

    results = search_items(
        status=status,
        suchtext=search,
    )

    if not results:

        st.info(
            "Keine Fundstücke gefunden."
        )

        return

    for item in results:

        with st.container(border=True):

            left, middle, right = st.columns(
                [1, 3, 2]
            )

            with left:

                if item.get("bildpfad"):

                    image = image_data_uri(
                        item["bildpfad"]
                    )

                    if image:

                        st.image(
                            image,
                            width=100,
                        )

            with middle:

                st.write(
                    f"### {item['kategorie']}"
                )

                st.write(
                    f"**ID:** #{item['id']}"
                )

                st.write(
                    f"**Fundort:** {item['fundort']}"
                )

                st.write(
                    f"**Datum:** {item['funddatum']}"
                )

                if item.get("farbe"):
                    st.write(
                        f"**Farbe:** {item['farbe']}"
                    )

            with right:

                if item["status"] == "Verfügbar":

                    if st.button(
                        "Als abgeholt markieren",
                        key=f"collect_{item['id']}",
                        use_container_width=True,
                    ):

                        update_item_status(
                            item["id"],
                            "Abgeholt",
                        )

                        st.rerun()

                else:

                    if st.button(
                        "Wieder verfügbar",
                        key=f"available_{item['id']}",
                        use_container_width=True,
                    ):

                        update_item_status(
                            item["id"],
                            "Verfügbar",
                        )

                        st.rerun()

                if st.button(
                    "Fundstück löschen",
                    key=f"delete_{item['id']}",
                    use_container_width=True,
                ):

                    image_path = item.get(
                        "bildpfad"
                    )

                    delete_item(
                        item["id"]
                    )

                    if image_path:

                        try:

                            path = Path(
                                image_path
                            )

                            if path.exists():
                                path.unlink()

                        except Exception:
                            pass

                    st.rerun()


# ============================================================
# INFORMATIONEN
# ============================================================

def render_info():

    st.title("Informationen")

    st.write(
        "Alles Wichtige über das digitale Fundbüro."
    )

    st.info(
        """
        Das Kath. FundBüro ist eine digitale Lösung
        zur Verwaltung verlorener und gefundener
        Gegenstände am Katharineum.
        """
    )

    st.subheader("Wie funktioniert die KI?")

    st.write(
        """
        Beim Erfassen eines Fundstücks kann ein Foto
        hochgeladen werden. Das KI-Modell analysiert
        das Bild und schlägt eine passende Kategorie vor.

        Die vorgeschlagene Kategorie kann anschließend
        kontrolliert und verändert werden.
        """
    )

    st.subheader("Welche Informationen werden gespeichert?")

    st.write(
        """
        Zu jedem Fundstück können Kategorie, Farbe,
        Größe, Fundort, Funddatum, Beschreibung,
        Foto und die KI-Erkennung gespeichert werden.
        """
    )


# ============================================================
# ROUTING
# ============================================================

PAGES = {
    "Startseite": render_home,
    "Fundstück erfassen": render_add_item,
    "Fundstücke suchen": render_search,
    "Fundbüro verwalten": render_admin,
    "Informationen": render_info,
}


def main():

    render_navigation()

    page = st.session_state.get(
        "page",
        "Startseite",
    )

    render_function = PAGES.get(
        page,
        render_home,
    )

    render_function()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
