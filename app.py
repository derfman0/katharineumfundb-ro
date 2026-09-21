import base64
import html
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
# ORDNER / DATENBANK
# ============================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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

DEFAULT_SESSION_STATE = {
    "page": "Startseite",
    "uploaded_image": None,
    "image_path": None,
    "ai_result": None,
    "ai_top_results": [],
    "processed_file_id": None,
    "form_reset": 0,
}

for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    :root {
        --red: #c8102e;
        --red-dark: #a50d26;
        --red-light: #fff1f3;

        --black: #171717;
        --text: #202124;
        --muted: #6b7280;

        --background: #f6f7f8;
        --white: #ffffff;
        --border: #e5e7eb;

        --green: #16803c;
        --green-bg: #e9f8ef;

        --blue: #2563eb;
        --blue-bg: #edf4ff;

        --shadow: 0 8px 30px rgba(20, 20, 20, 0.06);
    }


    html,
    body,
    [class*="css"] {
        font-family:
            'Inter',
            -apple-system,
            BlinkMacSystemFont,
            'Segoe UI',
            sans-serif;
    }


    .stApp {
        background: var(--background);
        color: var(--text);
    }


    .main .block-container {
        max-width: 1280px;
        padding-top: 0.5rem;
        padding-bottom: 4rem;
    }


    #MainMenu {
        visibility: hidden;
    }


    footer {
        visibility: hidden;
    }


    header[data-testid="stHeader"] {
        background: transparent;
    }


    section[data-testid="stSidebar"] {
        display: none;
    }


    /* =====================================================
       TOPBAR
       ===================================================== */

    .topbar {
        background: rgba(255, 255, 255, 0.97);
        border-bottom: 1px solid var(--border);

        min-height: 76px;

        display: flex;
        align-items: center;

        padding: 0 28px;

        margin: -0.5rem -2rem 1.5rem -2rem;

        position: sticky;
        top: 0;

        z-index: 100;
    }


    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }


    .brand-mark {
        width: 42px;
        height: 42px;

        background: var(--red);
        color: white;

        border-radius: 12px;

        display: flex;
        align-items: center;
        justify-content: center;

        font-weight: 800;
        font-size: 17px;
    }


    .brand-title {
        font-size: 18px;
        font-weight: 800;
        color: var(--black);
        line-height: 1.1;
    }


    .brand-subtitle {
        font-size: 11px;
        color: var(--muted);
        margin-top: 3px;
    }


    /* =====================================================
       BUTTONS
       ===================================================== */

    .stButton > button {
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
        background: white !important;
        color: var(--text) !important;

        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;

        min-height: 42px !important;

        transition: all 0.15s ease !important;
    }


    .stButton > button:hover {
        border-color: var(--red) !important;
        color: var(--red) !important;

        transform: translateY(-1px);

        box-shadow:
            0 5px 15px rgba(200, 16, 46, 0.08);
    }


    .primary-button > button {
        background: var(--red) !important;
        color: white !important;
        border-color: var(--red) !important;
        font-weight: 700 !important;
    }


    .primary-button > button:hover {
        background: var(--red-dark) !important;
        color: white !important;
        border-color: var(--red-dark) !important;
    }


    .nav-button > button {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;

        font-size: 13px !important;
        min-height: 38px !important;

        color: #555 !important;
    }


    .nav-button > button:hover {
        color: var(--red) !important;
        background: var(--red-light) !important;
    }


    /* =====================================================
       TITLES
       ===================================================== */

    .eyebrow {
        color: var(--red);

        font-size: 12px;
        font-weight: 800;

        text-transform: uppercase;
        letter-spacing: 0.08em;

        margin-bottom: 8px;
    }


    .page-title {
        font-size: 36px;
        line-height: 1.12;

        font-weight: 800;
        letter-spacing: -1.5px;

        color: var(--black);

        margin-bottom: 8px;
    }


    .page-subtitle {
        font-size: 15px;
        line-height: 1.6;

        color: var(--muted);

        max-width: 650px;

        margin-bottom: 28px;
    }


    /* =====================================================
       HERO
       ===================================================== */

    .hero {
        background:
            linear-gradient(
                100deg,
                #ffffff 0%,
                #ffffff 55%,
                #fff4f6 100%
            );

        border: 1px solid var(--border);
        border-radius: 24px;

        padding: 48px;

        margin-bottom: 24px;

        box-shadow: var(--shadow);

        position: relative;
        overflow: hidden;
    }


    .hero::after {
        content: "";

        position: absolute;

        right: -100px;
        top: -100px;

        width: 300px;
        height: 300px;

        border-radius: 50%;

        background:
            rgba(200, 16, 46, 0.05);
    }


    .hero-accent {
        width: 64px;
        height: 5px;

        background: var(--red);

        border-radius: 10px;

        margin-bottom: 20px;
    }


    .hero-small {
        color: var(--red);

        font-size: 12px;
        font-weight: 800;

        text-transform: uppercase;
        letter-spacing: 0.08em;

        margin-bottom: 8px;
    }


    .hero-title {
        font-size: 48px;

        font-weight: 800;

        line-height: 1.03;

        letter-spacing: -2.5px;

        color: var(--black);

        margin-bottom: 16px;

        position: relative;
        z-index: 2;
    }


    .hero-text {
        color: var(--muted);

        font-size: 16px;
        line-height: 1.7;

        max-width: 570px;

        position: relative;
        z-index: 2;
    }


    /* =====================================================
       ACTION CARDS
       ===================================================== */

    .action-card {
        background: white;

        border: 1px solid var(--border);
        border-radius: 18px;

        padding: 28px;

        min-height: 245px;

        box-shadow:
            0 4px 20px rgba(0, 0, 0, 0.035);
    }


    .action-icon {
        width: 48px;
        height: 48px;

        border-radius: 14px;

        background: var(--red-light);
        color: var(--red);

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 21px;
        font-weight: 700;

        margin-bottom: 20px;
    }


    .action-title {
        font-size: 19px;
        font-weight: 750;

        margin-bottom: 9px;

        color: var(--black);
    }


    .action-text {
        color: var(--muted);

        font-size: 13px;
        line-height: 1.6;

        min-height: 60px;
    }


    /* =====================================================
       SECTION
       ===================================================== */

    .section-title {
        font-size: 20px;
        font-weight: 750;

        color: var(--black);

        margin-top: 36px;
        margin-bottom: 16px;
    }


    /* =====================================================
       STATISTICS
       ===================================================== */

    .stat-card {
        background: white;

        border: 1px solid var(--border);
        border-radius: 16px;

        padding: 22px;

        box-shadow:
            0 3px 18px rgba(0, 0, 0, 0.035);
    }


    .stat-label {
        color: var(--muted);

        font-size: 12px;
        font-weight: 600;

        margin-bottom: 8px;
    }


    .stat-number {
        font-size: 30px;

        font-weight: 800;

        letter-spacing: -1px;

        color: var(--black);
    }


    .stat-description {
        color: #9ca3af;

        font-size: 11px;

        margin-top: 3px;
    }


    /* =====================================================
       SEARCH
       ===================================================== */

    .search-box {
        background: white;

        border: 1px solid var(--border);
        border-radius: 16px;

        padding: 8px;

        box-shadow: var(--shadow);

        margin-bottom: 18px;
    }


    /* =====================================================
       ITEM CARDS
       ===================================================== */

    .item-card {
        background: white;

        border: 1px solid var(--border);
        border-radius: 16px;

        overflow: hidden;

        box-shadow:
            0 4px 20px rgba(0, 0, 0, 0.04);

        height: 100%;
    }


    .item-image {
        width: 100%;
        height: 185px;

        object-fit: cover;

        display: block;

        background: #f1f1f1;
    }


    .item-image-placeholder {
        width: 100%;
        height: 185px;

        background: #f1f2f4;

        display: flex;
        align-items: center;
        justify-content: center;

        color: #9ca3af;

        font-size: 13px;
    }


    .item-content {
        padding: 17px;
    }


    .item-category {
        color: var(--black);

        font-weight: 750;
        font-size: 15px;

        margin-bottom: 9px;
    }


    .item-meta {
        color: var(--muted);

        font-size: 11px;

        line-height: 1.8;
    }


    .status {
        display: inline-flex;
        align-items: center;

        gap: 5px;

        border-radius: 999px;

        padding: 5px 10px;

        font-size: 10px;
        font-weight: 700;

        margin-top: 10px;
    }


    .status-available {
        background: var(--green-bg);
        color: var(--green);
    }


    .status-collected {
        background: var(--blue-bg);
        color: var(--blue);
    }


    /* =====================================================
       INFO / ADMIN / UPLOAD
       ===================================================== */

    .info-box,
    .admin-panel,
    .upload-panel {
        background: white;

        border: 1px solid var(--border);
        border-radius: 18px;

        padding: 26px;

        margin-bottom: 16px;

        box-shadow: var(--shadow);
    }


    .info-title {
        font-size: 17px;
        font-weight: 750;

        margin-bottom: 8px;
    }


    .info-text {
        color: var(--muted);

        font-size: 13px;
        line-height: 1.7;
    }


    .ai-box {
        border: 1px solid #f1c5cc;

        background: #fff8f9;

        border-radius: 16px;

        padding: 20px;

        margin-top: 20px;
    }


    .ai-label {
        color: var(--red);

        font-size: 11px;

        text-transform: uppercase;

        font-weight: 800;

        letter-spacing: 0.08em;
    }


    .ai-result {
        color: var(--black);

        font-size: 22px;

        font-weight: 800;

        margin-top: 6px;
    }


    .confidence {
        color: var(--muted);

        font-size: 12px;

        margin-top: 5px;
    }


    /* =====================================================
       MOBILE
       ===================================================== */

    @media (max-width: 800px) {

        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .topbar {
            margin-left: -1rem;
            margin-right: -1rem;

            padding: 0 15px;
        }

        .hero {
            padding: 30px 24px;
        }

        .hero-title {
            font-size: 36px;
        }

        .page-title {
            font-size: 30px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def set_page(page_name):
    st.session_state.page = page_name
    st.rerun()


@st.cache_data(show_spinner=False)
def image_to_data_uri(path):
    """Wandelt ein lokales Bild in eine Data-URI um."""

    try:
        file_path = Path(path)

        if not file_path.exists():
            return None

        suffix = file_path.suffix.lower()

        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }

        mime = mime_types.get(
            suffix,
            "image/jpeg",
        )

        encoded = base64.b64encode(
            file_path.read_bytes()
        ).decode("utf-8")

        return f"data:{mime};base64,{encoded}"

    except Exception:
        return None


def status_html(status):
    if status == "Verfügbar":
        return """
        <span class="status status-available">
            ● Verfügbar
        </span>
        """

    return """
    <span class="status status-collected">
        ● Abgeholt
    </span>
    """


def normalize_top_results(results):
    normalized = []

    if not results:
        return normalized

    for result in results:

        if isinstance(result, dict):
            label = result.get("label", "")
            score = result.get("score", 0)

        elif isinstance(result, (tuple, list)):

            if len(result) < 2:
                continue

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


def reset_upload_form():
    st.session_state.uploaded_image = None
    st.session_state.image_path = None
    st.session_state.ai_result = None
    st.session_state.ai_top_results = []
    st.session_state.processed_file_id = None
    st.session_state.form_reset += 1


# ============================================================
# NAVIGATION
# ============================================================

def render_navigation():

    st.markdown(
        """
        <div class="topbar">

            <div class="brand">

                <div class="brand-mark">
                    KF
                </div>

                <div>

                    <div class="brand-title">
                        Kath. FundBüro
                    </div>

                    <div class="brand-subtitle">
                        Digitales Fundbüro · Katharineum
                    </div>

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    nav1, nav2, nav3, nav4, nav5, nav6 = st.columns(
        [1.8, 1, 1, 1.1, 1, 1.1]
    )

    with nav1:
        st.markdown(
            """
            <div style="
                color:#6b7280;
                font-size:12px;
                padding-top:12px;
            ">
                Digitales Fundbüro
            </div>
            """,
            unsafe_allow_html=True,
        )

    navigation = [
        (nav2, "Startseite", "nav_home"),
        (nav3, "Suchen", "nav_search"),
        (nav4, "Erfassen", "nav_add"),
        (nav5, "Verwaltung", "nav_admin"),
        (nav6, "Informationen", "nav_info"),
    ]

    for column, label, key in navigation:

        with column:

            st.markdown(
                '<div class="nav-button">',
                unsafe_allow_html=True,
            )

            if st.button(
                label,
                key=key,
                use_container_width=True,
            ):
                set_page(
                    {
                        "Startseite": "Startseite",
                        "Suchen": "Fundstücke suchen",
                        "Erfassen": "Fundstück erfassen",
                        "Verwaltung": "Fundbüro verwalten",
                        "Informationen": "Informationen",
                    }[label]
                )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

    st.divider()


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
        """
        <div class="section-title">
            Was möchtest du machen?
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(
        3,
        gap="large",
    )

    # --------------------------------------------------------
    # Erfassen
    # --------------------------------------------------------

    with col1:

        st.markdown(
            """
            <div class="action-card">

                <div class="action-icon">
                    +
                </div>

                <div class="action-title">
                    Fundstück erfassen
                </div>

                <div class="action-text">
                    Fotografiere einen gefundenen Gegenstand.
                    Die KI unterstützt dich bei der Erkennung.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="primary-button">',
            unsafe_allow_html=True,
        )

        if st.button(
            "Fundstück erfassen",
            key="home_add",
            use_container_width=True,
        ):
            set_page("Fundstück erfassen")

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # Suche
    # --------------------------------------------------------

    with col2:

        st.markdown(
            """
            <div class="action-card">

                <div class="action-icon">
                    🔎
                </div>

                <div class="action-title">
                    Fundstücke suchen
                </div>

                <div class="action-text">
                    Durchsuche das Fundbüro nach Kategorie,
                    Fundort, Farbe oder Suchbegriff.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Fundstücke suchen",
            key="home_search",
            use_container_width=True,
        ):
            set_page("Fundstücke suchen")

    # --------------------------------------------------------
    # Verwaltung
    # --------------------------------------------------------

    with col3:

        st.markdown(
            """
            <div class="action-card">

                <div class="action-icon">
                    📋
                </div>

                <div class="action-title">
                    Fundbüro verwalten
                </div>

                <div class="action-text">
                    Fundstücke verwalten, Status ändern
                    und den Überblick behalten.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Verwaltungsbereich",
            key="home_admin",
            use_container_width=True,
        ):
            set_page("Fundbüro verwalten")

    # --------------------------------------------------------
    # Statistik
    # --------------------------------------------------------

    stats = get_statistics()

    st.markdown(
        """
        <div class="section-title">
            Aktueller Überblick
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2, s3 = st.columns(3)

    with s1:

        st.markdown(
            f"""
            <div class="stat-card">

                <div class="stat-label">
                    Gesamte Fundstücke
                </div>

                <div class="stat-number">
                    {stats["total"]}
                </div>

                <div class="stat-description">
                    gespeicherte Fundstücke
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with s2:

        st.markdown(
            f"""
            <div class="stat-card">

                <div class="stat-label">
                    Verfügbar
                </div>

                <div class="stat-number">
                    {stats["available"]}
                </div>

                <div class="stat-description">
                    aktuell im Fundbüro
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with s3:

        st.markdown(
            f"""
            <div class="stat-card">

                <div class="stat-label">
                    Abgeholt
                </div>

                <div class="stat-number">
                    {stats["collected"]}
                </div>

                <div class="stat-description">
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

    st.markdown(
        """
        <div class="eyebrow">
            Neues Fundstück
        </div>

        <div class="page-title">
            Fundstück erfassen
        </div>

        <div class="page-subtitle">
            Lade ein Foto hoch, lass die KI den Gegenstand erkennen
            und ergänze anschließend die wichtigsten Informationen.
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(
        [1.7, 1],
        gap="large",
    )

    with left:

        st.markdown(
            """
            <div class="upload-panel">

                <div style="
                    font-size:18px;
                    font-weight:750;
                    margin-bottom:5px;
                ">
                    Foto des Fundstücks
                </div>

                <div style="
                    color:#6b7280;
                    font-size:13px;
                    margin-bottom:20px;
                ">
                    Ein klares Foto hilft der KI bei der Erkennung.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        reset_suffix = st.session_state.form_reset

        uploaded_file = st.file_uploader(
            "Foto auswählen",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
            label_visibility="collapsed",
            key=f"file_uploader_{reset_suffix}",
        )

        camera_file = st.camera_input(
            "Oder direkt mit der Kamera aufnehmen",
            key=f"camera_input_{reset_suffix}",
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
                    f"{selected_file.name}:"
                    f"{len(selected_file.getvalue())}"
                )

            if (
                file_id
                != st.session_state.processed_file_id
            ):

                image_bytes = selected_file.getvalue()

                st.session_state.uploaded_image = image_bytes

                suffix = Path(
                    selected_file.name
                ).suffix.lower()

                filename = (
                    f"{uuid4().hex}{suffix}"
                )

                image_path = (
                    UPLOAD_DIR / filename
                )

                image_path.write_bytes(
                    image_bytes
                )

                st.session_state.image_path = str(
                    image_path
                )

                st.session_state.processed_file_id = file_id

                st.session_state.ai_result = None
                st.session_state.ai_top_results = []

            st.image(
                st.session_state.uploaded_image,
                caption="Ausgewähltes Foto",
                use_container_width=True,
            )

            st.markdown(
                '<div class="primary-button">',
                unsafe_allow_html=True,
            )

            if st.button(
                "KI-Erkennung starten",
                key="run_ai",
                use_container_width=True,
            ):

                try:

                    with st.spinner(
                        "Die KI analysiert das Fundstück ..."
                    ):

                        label, confidence, top_results = (
                            predict_image(selected_file)
                        )

                    st.session_state.ai_result = (
                        label,
                        confidence,
                    )

                    st.session_state.ai_top_results = (
                        normalize_top_results(
                            top_results
                        )
                    )

                    st.success(
                        "KI-Erkennung abgeschlossen."
                    )

                except Exception as error:

                    st.error(
                        "Die KI-Erkennung konnte "
                        f"nicht durchgeführt werden: {error}"
                    )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

    with right:

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
                        {html.escape(str(label))}
                    </div>

                    <div class="confidence">
                        Erkennungswahrscheinlichkeit:
                        <strong>
                            {float(confidence) * 100:.0f}%
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

                st.markdown(
                    """
                    <div style="
                        margin-top:20px;
                        font-size:13px;
                        font-weight:700;
                    ">
                        Weitere Möglichkeiten
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                for item in top_results[:4]:

                    st.markdown(
                        f"""
                        <div style="
                            display:flex;
                            justify-content:space-between;
                            padding:9px 0;
                            border-bottom:1px solid #eee;
                            font-size:12px;
                        ">

                            <span>
                                {html.escape(item["label"])}
                            </span>

                            <span style="
                                color:#6b7280;
                            ">
                                {item["score"] * 100:.0f}%
                            </span>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        else:

            st.markdown(
                """
                <div class="info-box">

                    <div class="info-title">
                        Noch keine KI-Erkennung
                    </div>

                    <div class="info-text">
                        Lade zunächst ein Foto hoch und starte
                        anschließend die KI-Erkennung.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # Angaben
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="section-title">
            Angaben zum Fundstück
        </div>
        """,
        unsafe_allow_html=True,
    )

    form_col1, form_col2 = st.columns(
        2,
        gap="large",
    )

    with form_col1:

        detected_category = (
            "Sonstiger Gegenstand"
        )

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

        category_index = (
            category_options.index(
                detected_category
            )
        )

        kategorie = st.selectbox(
            "Kategorie",
            category_options,
            index=category_index,
        )

        farbe = st.text_input(
            "Farbe",
            placeholder="z. B. blau, schwarz, rot ...",
        )

        groesse = st.text_input(
            "Größe",
            placeholder="z. B. M, 42, klein ...",
        )

    with form_col2:

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
            height=110,
        )

    st.markdown(
        '<div class="primary-button">',
        unsafe_allow_html=True,
    )

    if st.button(
        "Fundstück speichern",
        key="save_item",
        use_container_width=True,
    ):

        if st.session_state.image_path is None:

            st.warning(
                "Bitte lade zuerst ein Foto "
                "des Fundstücks hoch."
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
                    "Das Fundstück wurde "
                    "erfolgreich gespeichert."
                )

                reset_upload_form()

                st.rerun()

            except Exception as error:

                st.error(
                    "Beim Speichern ist ein Fehler "
                    f"aufgetreten: {error}"
                )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# FUNDSTÜCK-KARTE
# ============================================================

def render_item_card(item):

    image_uri = None

    if item["bildpfad"]:
        image_uri = image_to_data_uri(
            item["bildpfad"]
        )

    if image_uri:

        image_html = (
            f'<img class="item-image" '
            f'src="{image_uri}">'
        )

    else:

        image_html = """
        <div class="item-image-placeholder">
            Kein Foto verfügbar
        </div>
        """

    farbe = ""

    if item["farbe"]:
        farbe = (
            f'Farbe: '
            f'{html.escape(str(item["farbe"]))}'
            f'<br>'
        )

    st.markdown(
        f"""
        <div class="item-card">

            {image_html}

            <div class="item-content">

                <div class="item-category">
                    {html.escape(str(item["kategorie"]))}
                </div>

                <div class="item-meta">

                    {farbe}

                    Fundort:
                    {html.escape(str(item["fundort"]))}

                    <br>

                    Datum:
                    {html.escape(str(item["funddatum"]))}

                </div>

                {status_html(item["status"])}

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SUCHEN
# ============================================================

def render_search():

    st.markdown(
        """
        <div class="eyebrow">
            Fundbüro
        </div>

        <div class="page-title">
            Fundstücke suchen
        </div>

        <div class="page-subtitle">
            Durchsuche das Fundbüro nach verlorenen Gegenständen.
            Nutze Suchbegriffe und Filter, um schneller fündig zu werden.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="search-box">',
        unsafe_allow_html=True,
    )

    search_text = st.text_input(
        "Suche",
        placeholder=(
            "Wonach suchst du? "
            "z. B. Rucksack, blau, Sporthalle ..."
        ),
        label_visibility="collapsed",
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    f1, f2, f3 = st.columns(3)

    with f1:

        search_category = st.selectbox(
            "Kategorie",
            ["Alle"] + list(CATEGORIES),
        )

    with f2:

        search_location = st.selectbox(
            "Fundort",
            FUNDORTE_FILTER,
        )

    with f3:

        search_status = st.selectbox(
            "Status",
            STATUS_OPTIONEN,
        )

    results = search_items(
        kategorie=search_category,
        fundort=search_location,
        status=search_status,
        suchtext=search_text,
    )

    st.markdown(
        f"""
        <div class="section-title">
            {len(results)} Fundstücke gefunden
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not results:

        st.markdown(
            """
            <div class="info-box">

                <div class="info-title">
                    Keine Fundstücke gefunden
                </div>

                <div class="info-text">
                    Versuche einen anderen Suchbegriff
                    oder ändere deine Filter.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    for start in range(
        0,
        len(results),
        4,
    ):

        row_items = results[
            start:start + 4
        ]

        cols = st.columns(
            4,
            gap="medium",
        )

        for col, item in zip(
            cols,
            row_items,
        ):

            with col:
                render_item_card(item)


# ============================================================
# VERWALTUNG
# ============================================================

def render_admin_stat(
    label,
    value,
    description,
):

    st.markdown(
        f"""
        <div class="stat-card">

            <div class="stat-label">
                {label}
            </div>

            <div class="stat-number">
                {value}
            </div>

            <div class="stat-description">
                {description}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_admin_row(item):

    item_id = item["id"]

    st.markdown(
        '<div class="admin-panel">',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(
        [0.8, 2.2, 2.2, 2.3]
    )

    with c1:

        if item["bildpfad"]:

            image_uri = image_to_data_uri(
                item["bildpfad"]
            )

            if image_uri:
                st.image(
                    image_uri,
                    width=75,
                )

    with c2:

        st.markdown(
            f"""
            <div style="
                font-weight:750;
                margin-bottom:5px;
            ">
                {html.escape(str(item["kategorie"]))}
            </div>

            <div style="
                color:#6b7280;
                font-size:12px;
            ">
                ID #{item_id}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            f"""
            <div style="
                color:#6b7280;
                font-size:12px;
                line-height:1.8;
            ">

                Fundort:
                <strong style="color:#222">
                    {html.escape(str(item["fundort"]))}
                </strong>

                <br>

                Datum:
                <strong style="color:#222">
                    {html.escape(str(item["funddatum"]))}
                </strong>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:

        if item["status"] == "Verfügbar":

            if st.button(
                "Als abgeholt markieren",
                key=f"collect_{item_id}",
                use_container_width=True,
            ):

                update_item_status(
                    item_id,
                    "Abgeholt",
                )

                st.rerun()

        else:

            if st.button(
                "Wieder verfügbar",
                key=f"available_{item_id}",
                use_container_width=True,
            ):

                update_item_status(
                    item_id,
                    "Verfügbar",
                )

                st.rerun()

        if st.button(
            "Fundstück löschen",
            key=f"delete_{item_id}",
            use_container_width=True,
        ):

            image_path = item["bildpfad"]

            delete_item(item_id)

            if image_path:

                try:

                    path = Path(image_path)

                    if path.exists():
                        path.unlink()

                except Exception:
                    pass

            image_to_data_uri.clear()

            st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


def render_admin():

    st.markdown(
        """
        <div class="eyebrow">
            Verwaltung
        </div>

        <div class="page-title">
            Fundbüro verwalten
        </div>

        <div class="page-subtitle">
            Verwalte alle Fundstücke, aktualisiere den Status
            und behalte den Überblick über das Fundbüro.
        </div>
        """,
        unsafe_allow_html=True,
    )

    stats = get_statistics()

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        render_admin_stat(
            "Gesamt",
            stats["total"],
            "Fundstücke",
        )

    with a2:
        render_admin_stat(
            "Verfügbar",
            stats["available"],
            "Noch vorhanden",
        )

    with a3:
        render_admin_stat(
            "Abgeholt",
            stats["collected"],
            "Bereits zurückgegeben",
        )

    with a4:
        render_admin_stat(
            "Trinkflaschen",
            stats["bottles"],
            "gespeicherte Flaschen",
        )

    st.markdown(
        """
        <div class="section-title">
            Alle Fundstücke
        </div>
        """,
        unsafe_allow_html=True,
    )

    admin_search = st.text_input(
        "Fundstücke durchsuchen",
        placeholder=(
            "Nach Kategorie, Farbe, Beschreibung "
            "oder Fundort suchen ..."
        ),
    )

    admin_status = st.selectbox(
        "Status filtern",
        STATUS_OPTIONEN,
    )

    admin_results = search_items(
        status=admin_status,
        suchtext=admin_search,
    )

    if not admin_results:

        st.markdown(
            """
            <div class="info-box">

                <div class="info-title">
                    Keine Fundstücke
                </div>

                <div class="info-text">
                    Es wurden keine passenden Fundstücke gefunden.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    for item in admin_results:
        render_admin_row(item)


# ============================================================
# INFORMATIONEN
# ============================================================

def render_info():

    st.markdown(
        """
        <div class="eyebrow">
            Katharineum
        </div>

        <div class="page-title">
            Informationen
        </div>

        <div class="page-subtitle">
            Alles Wichtige über das digitale Fundbüro.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="info-box">

            <div class="info-title">
                Was ist das Kath. FundBüro?
            </div>

            <div class="info-text">
                Das Kath. FundBüro ist eine digitale Lösung
                zur Verwaltung verlorener und gefundener
                Gegenstände am Katharineum.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="info-box">

            <div class="info-title">
                Wie funktioniert die KI?
            </div>

            <div class="info-text">
                Beim Erfassen eines Fundstücks kann ein Foto
                hochgeladen werden. Ein KI-Modell analysiert
                das Bild und schlägt eine passende Kategorie vor.
                Die vorgeschlagene Kategorie kann anschließend
                kontrolliert und verändert werden.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="info-box">

            <div class="info-title">
                Was passiert mit den Daten?
            </div>

            <div class="info-text">
                Die Fundstücke werden in der Datenbank des
                digitalen Fundbüros gespeichert. Zu jedem
                Fundstück können unter anderem Kategorie,
                Farbe, Größe, Fundort, Datum, Beschreibung
                und Foto hinterlegt werden.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
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

    render_page = PAGES.get(
        st.session_state.page,
        render_home,
    )

    render_page()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
