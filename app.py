import os
from datetime import date
from pathlib import Path

from PIL import Image
import streamlit as st

from ai_model import predict_image
from database import (
    delete_item,
    get_all_items,
    get_statistics,
    init_database,
    save_item,
    search_items,
    update_item_status,
)

# ============================================================
# GRUNDKONFIGURATION
# ============================================================

st.set_page_config(
    page_title="KathFundBüro",
    page_icon="🎒",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# VERZEICHNISSE & DATENBANK
# ============================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

init_database()


# ============================================================
# KATEGORIEN
# ============================================================

CATEGORIES = [
    "Trinkflasche",
    "Brotdose",
    "Federtasche",
    "Bleistift",
    "Kugelschreiber",
    "Füller",
    "Textmarker",
    "Filzstift",
    "Buntstift",
    "Radiergummi",
    "Spitzer",
    "Lineal",
    "Geodreieck",
    "Zirkel",
    "Schere",
    "Klebestift",
    "Notizbuch",
    "Collegeblock",
    "Hausaufgabenheft",
    "Mappe",
    "Ordner",
    "Schnellhefter",
    "Buch",
    "Schulbuch",
    "Taschenrechner",
    "Handy",
    "Kopfhörer",
    "Ladekabel",
    "Powerbank",
    "USB-Stick",
    "Schlüssel",
    "Portemonnaie",
    "Brille",
    "Sonnenbrille",
    "Regenschirm",
    "Fahrradhelm",
    "Rucksack",
    "Sporttasche",
    "Turnbeutel",
    "Jacke",
    "Hoodie",
    "Pullover",
    "T-Shirt",
    "Hose",
    "Kurze Hose",
    "Schuhe",
    "Mütze",
    "Schal",
    "Handschuhe",
    "Sonstiger Gegenstand",
]


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 18px;
        color: #666;
        margin-top: 0;
        margin-bottom: 25px;
    }
    .info-box {
        padding: 20px;
        border-radius: 15px;
        background-color: #f5f7fa;
        margin-bottom: 20px;
    }
    .success-box {
        padding: 20px;
        border-radius: 15px;
        background-color: #eaf7ee;
        margin-bottom: 20px;
    }
    .warning-box {
        padding: 20px;
        border-radius: 15px;
        background-color: #fff8e6;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🎒 KathFundBüro")
    st.caption("Digitales Fundbüro des Katharineums")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "📷 Fundstück erfassen",
            "🔎 Fundstücke suchen",
            "🛠️ Fundbüro verwalten",
            "ℹ️ Informationen",
        ],
    )

    st.divider()

    st.caption("KathFundBüro")
    st.caption("Digitale Unterstützung für das schulische Fundbüro")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🎒 KathFundBüro</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">Das digitale Fundbüro des Katharineums</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SEITE 1: FUNDSTÜCK ERFASSEN
# ============================================================

if page == "📷 Fundstück erfassen":

    st.header("📷 Neues Fundstück erfassen")

    st.markdown(
        """
        Fotografiere einen gefundenen Gegenstand oder lade ein Bild hoch.
        Die KI versucht anschließend automatisch zu erkennen, um welchen
        Gegenstand es sich handelt.
        """
    )

    st.divider()

    # Bild aufnehmen / hochladen
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📸 Kamera")
        camera_image = st.camera_input("Fundstück fotografieren")

    with col2:
        st.subheader("📁 Bild hochladen")
        uploaded_image = st.file_uploader(
            "Bild auswählen",
            type=["jpg", "jpeg", "png", "webp"],
        )

    # Bild auswählen
    image = None
    if camera_image is not None:
        image = Image.open(camera_image)
    elif uploaded_image is not None:
        image = Image.open(uploaded_image)

    # Wenn Bild vorhanden
    if image is not None:
        st.divider()

        col_image, col_ai = st.columns([1, 1])

        with col_image:
            st.subheader("🖼️ Bild")
            st.image(
                image,
                caption="Ausgewähltes Fundstück",
                use_container_width=True,
            )

        # KI-Erkennung
        with col_ai:
            st.subheader("🤖 KI-Erkennung")

            if st.button(
                "🔍 Gegenstand erkennen",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Die KI analysiert das Bild..."):
                    try:
                        label, confidence, top_results = predict_image(image)

                        st.session_state["ai_label"] = label
                        st.session_state["ai_confidence"] = confidence
                        st.session_state["ai_results"] = top_results
                    except Exception as e:
                        st.error("Die KI konnte das Bild nicht analysieren.")
                        st.exception(e)

            # Ergebnis anzeigen
            if "ai_label" in st.session_state:
                label = st.session_state["ai_label"]
                confidence = st.session_state["ai_confidence"]

                st.success(f"Erkannt: **{label}**")

                st.metric(
                    "KI-Sicherheit",
                    f"{confidence * 100:.1f} %",
                )

                if "ai_results" in st.session_state:
                    with st.expander("Weitere KI-Ergebnisse anzeigen"):
                        for result in st.session_state["ai_results"]:
                            st.write(
                                f"**{result['label']}** – {result['score'] * 100:.1f} %"
                            )

        # Formular zum Speichern
        st.divider()
        st.subheader("📝 Angaben zum Fundstück")

        ai_label = st.session_state.get("ai_label", "Sonstiger Gegenstand")
        ai_confidence = st.session_state.get("ai_confidence", 0.0)

        col1, col2 = st.columns(2)

        with col1:
            category_index = 0
            if ai_label in CATEGORIES:
                category_index = CATEGORIES.index(ai_label)

            category = st.selectbox(
                "Kategorie",
                CATEGORIES,
                index=category_index,
            )

            color = st.text_input(
                "Farbe",
                placeholder="z. B. blau, schwarz, rot",
            )

            size = st.text_input(
                "Größe",
                placeholder="z. B. S, M, L oder keine Angabe",
            )

        with col2:
            location = st.text_input(
                "Fundort",
                placeholder="z. B. Raum 203, Sporthalle, Schulhof",
            )

            found_date = st.date_input(
                "Funddatum",
                value=date.today(),
            )

            description = st.text_area(
                "Weitere Beschreibung",
                placeholder="Besondere Merkmale, Aufkleber, Marke usw.",
            )

        st.divider()

        # Speichern-Button & Logik
        if st.button(
            "💾 Fundstück speichern",
            type="primary",
            use_container_width=True,
        ):
            if not location.strip():
                st.warning("Bitte gib einen Fundort an.")
            else:
                try:
                    filename = (
                        f"fundstueck_"
                        f"{date.today().strftime('%Y%m%d')}_"
                        f"{abs(hash(str(image))) % 100000}.jpg"
                    )

                    image_path = UPLOAD_DIR / filename

                    image.convert("RGB").save(
                        image_path,
                        quality=90,
                    )

                    # Datenbankaufruf (Korrekt eingerückt)
                    save_item(
                        kategorie=category,
                        farbe=color,
                        groesse=size,
                        fundort=location,
                        funddatum=str(found_date),
                        beschreibung=description,
                        bildpfad=str(image_path),
                        ki_konfidenz=ai_confidence,
                    )

                    st.success("✅ Das Fundstück wurde erfolgreich gespeichert!")

                    # KI-Daten aus Session State zurücksetzen
                    for key in ["ai_label", "ai_confidence", "ai_results"]:
                        if key in st.session_state:
                            del st.session_state[key]

                except Exception as e:
                    st.error("Beim Speichern ist ein Fehler aufgetreten.")
                    st.exception(e)


# ============================================================
# SEITE 2: FUNDSTÜCKE SUCHEN
# ============================================================

elif page == "🔎 Fundstücke suchen":

    st.header("🔎 Fundstücke suchen")
    st.write("Hier kannst du nach bereits erfassten Fundstücken suchen.")

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        search_text = st.text_input(
            "🔍 Suchbegriff",
            placeholder="z. B. blau, Sporthalle, Rucksack...",
        )

    with col2:
        search_category = st.selectbox(
            "Kategorie",
            ["Alle Kategorien"] + CATEGORIES,
        )

    with col3:
        search_status = st.selectbox(
            "Status",
            ["Alle", "Gefunden", "Abgeholt"],
        )

    st.divider()

    # Suchergebnis laden
    try:
        if search_text.strip() or search_category != "Alle Kategorien":
            items = search_items(
                search_text.strip(),
                None if search_category == "Alle Kategorien" else search_category,
            )
        else:
            items = get_all_items()
    except Exception as e:
        st.error("Die Fundstücke konnten nicht geladen werden.")
        st.exception(e)
        items = []

    # Status filtern
    if search_status != "Alle":
        items = [item for item in items if item.get("status") == search_status]

    st.subheader(f"📦 {len(items)} Fundstück(e) gefunden")

    if not items:
        st.info("Keine passenden Fundstücke gefunden.")
    else:
        for item in items:
            with st.container(border=True):
                col_image, col_info = st.columns([1, 2])

                with col_image:
                    image_path = item.get("bildpfad")
                    if image_path and os.path.exists(image_path):
                        st.image(image_path, use_container_width=True)
                    else:
                        st.info("Kein Bild vorhanden")

                with col_info:
                    st.markdown(f"### {item.get('kategorie', 'Unbekannt')}")
                    st.write(f"**Fundort:** {item.get('fundort', '-')}")
                    st.write(f"**Funddatum:** {item.get('funddatum', '-')}")

                    if item.get("farbe"):
                        st.write(f"**Farbe:** {item['farbe']}")

                    if item.get("groesse"):
                        st.write(f"**Größe:** {item['groesse']}")

                    if item.get("beschreibung"):
                        st.write(f"**Beschreibung:** {item['beschreibung']}")

                    status = item.get("status", "Gefunden")
                    if status == "Gefunden":
                        st.success("🟢 Noch im Fundbüro")
                    else:
                        st.info("🔵 Bereits abgeholt")


# ============================================================
# SEITE 3: ADMIN / VERWALTUNG
# ============================================================

elif page == "🛠️ Fundbüro verwalten":

    st.header("🛠️ Fundbüro verwalten")
    st.warning("Dieser Bereich ist für die Verwaltung des Fundbüros gedacht.")

    # Statistiken
    try:
        stats = get_statistics()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📦 Fundstücke", stats.get("gesamt", 0))
        with col2:
            st.metric("🟢 Noch vorhanden", stats.get("gefunden", 0))
        with col3:
            st.metric("🔵 Abgeholt", stats.get("abgeholt", 0))

    except Exception as e:
        st.error("Statistiken konnten nicht geladen werden.")
        st.exception(e)

    st.divider()

    # Alle Fundstücke
    st.subheader("📋 Fundstücke verwalten")

    try:
        items = get_all_items()
    except Exception as e:
        st.error("Fundstücke konnten nicht geladen werden.")
        st.exception(e)
        items = []

    if not items:
        st.info("Es sind noch keine Fundstücke vorhanden.")
    else:
        for item in items:
            with st.expander(
                f"#{item['id']} – {item.get('kategorie', 'Item')} – {item.get('status', 'Unbekannt')}"
            ):
                col1, col2 = st.columns([1, 2])

                with col1:
                    image_path = item.get("bildpfad")
                    if image_path and os.path.exists(image_path):
                        st.image(image_path, use_container_width=True)

                with col2:
                    st.write(f"**Kategorie:** {item.get('kategorie', '-')}")
                    st.write(f"**Fundort:** {item.get('fundort', '-')}")
                    st.write(f"**Funddatum:** {item.get('funddatum', '-')}")
                    st.write(f"**Status:** {item.get('status', '-')}")

                    if item.get("beschreibung"):
                        st.write(f"**Beschreibung:** {item['beschreibung']}")

                st.divider()

                # Status aktualisieren
                if item.get("status") == "Gefunden":
                    if st.button("✅ Als abgeholt markieren", key=f"picked_{item['id']}"):
                        update_item_status(item["id"], "Abgeholt")
                        st.success("Fundstück wurde als abgeholt markiert.")
                        st.rerun()
                else:
                    if st.button("↩️ Wieder als gefunden markieren", key=f"found_{item['id']}"):
                        update_item_status(item["id"], "Gefunden")
                        st.success("Fundstück ist wieder als gefunden markiert.")
                        st.rerun()

                # Löschen
                if st.button("🗑️ Fundstück löschen", key=f"delete_{item['id']}"):
                    image_path = item.get("bildpfad")
                    try:
                        delete_item(item["id"])
                        if image_path and os.path.exists(image_path):
                            os.remove(image_path)
                        st.success("Fundstück wurde gelöscht.")
                        st.rerun()
                    except Exception as e:
                        st.error("Fundstück konnte nicht gelöscht werden.")
                        st.exception(e)


# ============================================================
# SEITE 4: INFORMATIONEN
# ============================================================

elif page == "ℹ️ Informationen":

    st.header("ℹ️ Über das KathFundBüro")

    st.markdown(
        """
        ## 🎒 Was ist das KathFundBüro?

        Das KathFundBüro ist ein digitales Fundbüro für das Katharineum.

        Gefundene Gegenstände können fotografiert und anschließend
        digital erfasst werden.

        Eine künstliche Intelligenz versucht automatisch zu erkennen,
        um welchen Gegenstand es sich handelt.

        Dadurch können Fundstücke später einfacher wiedergefunden werden.
        """
    )

    st.divider()

    st.subheader("🤖 Die künstliche Intelligenz")

    st.markdown(
        """
        Für die Bilderkennung wird ein Hugging-Face-Modell verwendet.

        Das Modell analysiert das hochgeladene Foto und vergleicht es
        mit verschiedenen möglichen Gegenstandskategorien.

        Anschließend wird die wahrscheinlichste Kategorie angezeigt.
        """
    )

    st.info(
        "💡 Die KI ist eine Unterstützung. "
        "Die erkannte Kategorie kann vor dem Speichern jederzeit "
        "manuell geändert werden."
    )

    st.divider()

    st.subheader("📦 Die Kategorien")

    category_columns = st.columns(3)
    for index, category in enumerate(CATEGORIES):
        with category_columns[index % 3]:
            st.write(f"• {category}")

    st.divider()

    st.subheader("🔒 Datenschutz")

    st.markdown(
        """
        Die Anwendung sollte ausschließlich für schulische Fundstücke
        verwendet werden.

        Bitte fotografiere keine Personen und speichere keine unnötigen
        persönlichen Daten.
        """
    )

    st.divider()

    st.caption("KathFundBüro – Digitales Fundbüro des Katharineums")
