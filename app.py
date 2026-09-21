import base64
from datetime import date
import html
from pathlib import Path
from uuid import uuid4

import streamlit as st

from ai_model import CATEGORIES, predict_image
from database import (
    delete_item,
    get_all_items,
    get_statistics,
    init_database,
    save_item,
    search_items,
    update_item_status,
)

# =========================================================
# GRUNDKONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Kath. FundBüro",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# VERZEICHNISSE / DATENBANK
# =========================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

init_database()


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "Startseite"

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "image_path" not in st.session_state:
    st.session_state.image_path = None

if "ai_result" not in st.session_state:
    st.session_state.ai_result = None

if "ai_top_results" not in st.session_state:
    st.session_state.ai_top_results = []


# =========================================================
# DESIGN / CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GLOBAL
       ===================================================== */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

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

        --radius: 16px;
        --shadow: 0 8px 30px rgba(20, 20, 20, 0.06);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
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

    /* Streamlit UI reduzieren */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
    section[data-testid="stSidebar"] { display: none; }

    /* =====================================================
       TOP NAVIGATION
       ===================================================== */

    .topbar {
        background: rgba(255,255,255,0.97);
        border-bottom: 1px solid var(--border);
        height: 76px;
        display: flex;
        align-items: center;
        padding: 0 28px;
        margin: -0.5rem -2rem 2rem -2rem;
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
        font-size: 18px;
        letter-spacing: -1px;
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
        box-shadow: 0 5px 15px rgba(200,16,46,0.08);
    }

    .stButton > button[kind="primary"] {
        background: var(--red) !important;
        color: white !important;
        border-color: var(--red) !important;
        font-weight: 700 !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: var(--red-dark) !important;
        color: white !important;
        border-color: var(--red-dark) !important;
    }

    /* =====================================================
       TYPOGRAPHY & CARDS
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

    .hero {
        background: linear-gradient(100deg, rgba(255,255,255,1) 0%, rgba(255,255,255,0.98) 55%, rgba(255,244,246,1) 100%);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 48px;
        margin-bottom: 24px;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }

    .hero-title {
        font-size: 48px;
        font-weight: 800;
        line-height: 1.03;
        letter-spacing: -2.5px;
        color: var(--black);
        margin-bottom: 16px;
    }

    .hero-text {
        color: var(--muted);
        font-size: 16px;
        line-height: 1.7;
        max-width: 570px;
    }

    .action-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 28px;
        min-height: 220px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.035);
        margin-bottom: 15px;
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
        margin-bottom: 20px;
        font-weight: 700;
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
    }

    .stat-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 3px 18px rgba(0,0,0,0.035);
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

    .section-title {
        font-size: 20px;
        font-weight: 750;
        color: var(--black);
        margin-top: 36px;
        margin-bottom: 16px;
    }

    /* =====================================================
       ITEM CARDS
       ===================================================== */

    .item-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }

    .item-image {
        width: 100%;
        height: 185px;
        object-fit: cover;
        display: block;
        background: #f1f1f1;
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
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 10px;
        font-weight: 700;
        margin-top: 10px;
    }

    .status-available { background: var(--green-bg); color: var(--green); }
    .status-collected { background: var(--blue-bg); color: var(--blue); }

    .ai-box {
        border: 1px solid #f1c5cc;
        background: #fff8f9;
        border-radius: 16px;
        padding: 20px;
    }

    .ai-label {
        color: var(--red);
        font-size: 11px;
        text-transform: uppercase;
        font-weight: 800;
    }

    .ai-result {
        color: var(--black);
        font-size: 22px;
        font-weight: 800;
        margin-top: 6px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HILFSFUNKTIONEN
# =========================================================

def set_page(page_name: str):
    st.session_state.page = page_name
    st.rerun()


def reset_form():
    st.session_state.uploaded_image = None
    st.session_state.image_path = None
    st.session_state.ai_result = None
    st.session_state.ai_top_results = []


def image_to_data_uri(path: str):
    try:
        p = Path(path)
        if not p.exists():
            return None
        suffix = p.suffix.lower()
        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }.get(suffix, "image/jpeg")
        encoded = base64.b64encode(p.read_bytes()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return None


def status_html(status: str):
    if status == "Verfügbar":
        return '<span class="status status-available">● Verfügbar</span>'
    return '<span class="status status-collected">● Abgeholt</span>'


def normalize_top_results(results):
    normalized = []
    if not results:
        return normalized

    for result in results:
        if isinstance(result, dict):
            label = result.get("label", "")
            score = result.get("score", 0)
        elif isinstance(result, (tuple, list)) and len(result) >= 2:
            label, score = result[0], result[1]
        else:
            continue

        try:
            score = float(score)
        except Exception:
            score = 0.0

        normalized.append({"label": str(label), "score": score})

    return normalized


# =========================================================
# TOP NAVIGATION
# =========================================================

st.markdown(
    """
    <div class="topbar">
        <div class="brand">
            <div class="brand-mark">KF</div>
            <div>
                <div class="brand-title">Kath. FundBüro</div>
                <div class="brand-subtitle">Katharineum</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

nav1, nav2, nav3, nav4, nav5 = st.columns([2.3, 1.1, 1.1, 1.2, 1.0])

with nav1:
    st.markdown("<div style='color:#6b7280; font-size:12px; padding-top:12px;'>Digitales Fundbüro</div>", unsafe_allow_html=True)
with nav2:
    if st.button("Startseite", key="nav_home", use_container_width=True):
        set_page("Startseite")
with nav3:
    if st.button("Suchen", key="nav_search", use_container_width=True):
        set_page("Fundstücke suchen")
with nav4:
    if st.button("Erfassen", key="nav_add", use_container_width=True):
        set_page("Fundstück erfassen")
with nav5:
    if st.button("Verwaltung", key="nav_admin", use_container_width=True):
        set_page("Fundbüro verwalten")

st.divider()


# =========================================================
# STARTSEITE
# =========================================================

if st.session_state.page == "Startseite":

    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Willkommen im digitalen Fundbüro</div>
            <div class="hero-title">Kath. FundBüro</div>
            <div class="hero-text">
                Verlorene Gegenstände finden, Fundstücke melden und alles rund um das Fundbüro des Katharineums einfach verwalten.
            </div>
        </div>
        <div class="section-title">Was möchtest du machen?</div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">+</div>
                <div class="action-title">Fundstück erfassen</div>
                <div class="action-text">Fotografiere einen gefundenen Gegenstand. Unsere KI unterstützt dich bei der Erkennung.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Fundstück erfassen", key="home_add", use_container_width=True, type="primary"):
            set_page("Fundstück erfassen")

    with col2:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">⌕</div>
                <div class="action-title">Fundstücke suchen</div>
                <div class="action-text">Durchsuche das Fundbüro nach Kategorie, Fundort, Farbe oder Suchbegriff.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Fundstücke suchen", key="home_search", use_container_width=True):
            set_page("Fundstücke suchen")

    with col3:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">≡</div>
                <div class="action-title">Fundbüro verwalten</div>
                <div class="action-text">Fundstücke verwalten, Status ändern und den aktuellen Überblick behalten.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Verwaltungsbereich", key="home_admin", use_container_width=True):
            set_page("Fundbüro verwalten")

    stats = get_statistics()
    st.markdown('<div class="section-title">Aktueller Überblick</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)

    with s1:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Gesamte Fundstücke</div><div class="stat-number">{stats["total"]}</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Verfügbar</div><div class="stat-number">{stats["available"]}</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Abgeholt</div><div class="stat-number">{stats["collected"]}</div></div>', unsafe_allow_html=True)


# =========================================================
# FUNDSTÜCK ERFASSEN
# =========================================================

elif st.session_state.page == "Fundstück erfassen":

    st.markdown(
        """
        <div class="eyebrow">Neues Fundstück</div>
        <div class="page-title">Fundstück erfassen</div>
        <div class="page-subtitle">Lade ein Foto hoch, lass die KI den Gegenstand erkennen und ergänze anschließend die wichtigsten Informationen.</div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.7, 1], gap="large")

    with left:
        uploaded_file = st.file_uploader("Foto auswählen", type=["jpg", "jpeg", "png", "webp"])
        camera_file = st.camera_input("Oder direkt mit der Kamera aufnehmen")
        selected_file = camera_file or uploaded_file

        if selected_file is not None:
            image_bytes = selected_file.getvalue()
            st.session_state.uploaded_image = image_bytes
            st.image(image_bytes, caption="Ausgewähltes Foto", use_container_width=True)

            if st.button("KI-Erkennung starten", key="run_ai", use_container_width=True, type="primary"):
                try:
                    with st.spinner("Die KI analysiert das Fundstück ..."):
                        label, confidence, top_results = predict_image(selected_file)

                        # temporär speichern
                        filename = f"{uuid4().hex}{Path(selected_file.name if hasattr(selected_file, 'name') else 'cam.jpg').suffix.lower()}"
                        image_path = UPLOAD_DIR / filename
                        image_path.write_bytes(image_bytes)

                        st.session_state.image_path = str(image_path)
                        st.session_state.ai_result = (label, confidence)
                        st.session_state.ai_top_results = normalize_top_results(top_results)

                    st.success("KI-Erkennung abgeschlossen.")
                except Exception as e:
                    st.error(f"Fehler bei KI-Erkennung: {e}")

    with right:
        if st.session_state.ai_result:
            label, confidence = st.session_state.ai_result
            st.markdown(
                f"""
                <div class="ai-box">
                    <div class="ai-label">KI-Erkennung</div>
                    <div class="ai-result">{html.escape(str(label))}</div>
                    <div style="color:var(--muted); font-size:12px; margin-top:5px;">
                        Erkennungswahrscheinlichkeit: <strong>{confidence * 100:.0f}%</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Lade ein Foto hoch und starte die KI-Erkennung.")

    st.markdown('<div class="section-title">Angaben zum Fundstück</div>', unsafe_allow_html=True)

    with st.form("add_item_form"):
        form_col1, form_col2 = st.columns(2, gap="large")

        default_cat = st.session_state.ai_result[0] if st.session_state.ai_result else CATEGORIES[0]
        cat_index = CATEGORIES.index(default_cat) if default_cat in CATEGORIES else 0

        with form_col1:
            category = st.selectbox("Kategorie", options=CATEGORIES, index=cat_index)
            title = st.text_input("Titel / Beschreibung", value=default_cat if st.session_state.ai_result else "")
            location = st.text_input("Fundort (z.B. Sporthalle, Pausenhof)")

        with form_col2:
            color = st.text_input("Farbe")
            found_date = st.date_input("Funddatum", value=date.today())
            notes = st.text_area("Zusätzliche Anmerkungen")

        submitted = st.form_submit_button("Fundstück speichern", type="primary", use_container_width=True)

        if submitted:
            if not title or not location:
                st.error("Bitte fülle mindestens Titel und Fundort aus.")
            else:
                save_item(
                    title=title,
                    category=category,
                    location=location,
                    color=color,
                    found_date=str(found_date),
                    notes=notes,
                    image_path=st.session_state.image_path,
                )
                st.success("Fundstück erfolgreich gespeichert!")
                reset_form()
                st.rerun()


# =========================================================
# FUNDSTÜCKE SUCHEN
# =========================================================

elif st.session_state.page == "Fundstücke suchen":

    st.markdown('<div class="page-title">Fundstücke suchen</div>', unsafe_allow_html=True)

    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        query = st.text_input("Suchbegriff (Titel, Ort, Farbe)", placeholder="Suchen...")
    with s_col2:
        cat_filter = st.selectbox("Kategorie Filter", options=["Alle"] + CATEGORIES)

    items = search_items(query=query, category=None if cat_filter == "Alle" else cat_filter)

    st.write(f"**{len(items)}** Fundstücke gefunden")

    cols = st.columns(3)
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            img_uri = image_to_data_uri(item.get("image_path")) if item.get("image_path") else None
            img_html = f'<img src="{img_uri}" class="item-image"/>' if img_uri else '<div class="item-image" style="display:flex;align-items:center;justify-content:center;color:#aaa;">Kein Bild</div>'

            st.markdown(
                f"""
                <div class="item-card">
                    {img_html}
                    <div class="item-content">
                        <div class="item-category">{html.escape(item['title'])}</div>
                        <div class="item-meta">
                            Kategorie: {html.escape(item['category'])}<br/>
                            Ort: {html.escape(item['location'])}<br/>
                            Datum: {html.escape(str(item['found_date']))}
                        </div>
                        {status_html(item['status'])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# FUNDBÜRO VERWALTEN (ADMIN)
# =========================================================

elif st.session_state.page == "Fundbüro verwalten":

    st.markdown('<div class="page-title">Verwaltung</div>', unsafe_allow_html=True)

    items = get_all_items()

    if not items:
        st.info("Keine Fundstücke vorhanden.")
    else:
        for item in items:
            c1, c2, c3, c4 = st.columns([1, 3, 2, 2])
            with c1:
                st.write(f"**ID: {item['id']}**")
            with c2:
                st.write(f"**{item['title']}** ({item['category']})")
                st.caption(f"Ort: {item['location']} | Datum: {item['found_date']}")
            with c3:
                new_status = st.selectbox(
                    "Status",
                    options=["Verfügbar", "Abgeholt"],
                    index=0 if item["status"] == "Verfügbar" else 1,
                    key=f"status_{item['id']}",
                )
                if new_status != item["status"]:
                    update_item_status(item["id"], new_status)
                    st.rerun()
            with c4:
                if st.button("Löschen", key=f"del_{item['id']}"):
                    delete_item(item["id"])
                    st.rerun()
            st.divider()
