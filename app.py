import io
import uuid
from pathlib import Path
from datetime import date

import streamlit as st
from PIL import Image

from ai_model import load_labels, load_model, predict_image
from database import (
    init_database, save_item, get_all_items, search_items,
    update_item_status, delete_item, get_statistics
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"

st.set_page_config(page_title="KathFundBüro", page_icon="🔎", layout="wide")

st.markdown("""
<style>
.block-container {max-width:1250px; padding-top:1.5rem;}
.hero {background:linear-gradient(135deg,#e51d2a,#c91725); color:white;
padding:2rem; border-radius:24px; margin-bottom:1.5rem;}
.hero h1 {margin:0; font-size:2.7rem;}
.result-card {text-align:center; padding:2rem; border-radius:24px;
background:#e9f9fc; border:2px solid #45bfd2; margin:1rem 0;}
</style>
""", unsafe_allow_html=True)

def emoji(category):
    mapping = {"Trinkflasche":"🥤", "Hoodie":"🧥",
               "Federtasche":"✏️", "Kurzehose":"🩳"}
    return mapping.get(category, "📦")

def save_image(file_like):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.open(file_like).convert("RGB")
    path = UPLOAD_DIR / f"{uuid.uuid4().hex}.jpg"
    image.save(path, "JPEG", quality=90)
    return str(path)

@st.cache_resource
def ai_resources():
    return load_model(), load_labels()

try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_database()
except Exception as error:
    st.error("⚠️ Die Datenbank konnte nicht erstellt werden.")
    st.exception(error)
    st.stop()

try:
    model, labels = ai_resources()
    model_error = None
except Exception as error:
    model, labels, model_error = None, [], error

st.markdown('<div class="hero"><h1>🔎 KathFundBüro</h1><p>Das digitale Fundbüro für das Katharineum</p></div>', unsafe_allow_html=True)

page = st.sidebar.radio("Navigation", [
    "📷 Fundstück erfassen", "🔍 Fundstücke suchen",
    "📦 Übersicht", "ℹ️ Informationen"
])

if page == "📷 Fundstück erfassen":
    st.header("📷 Fundstück erfassen")
    st.write("Fotografiere einen gefundenen Gegenstand oder lade ein Bild hoch.")
    if model_error:
        st.error("⚠️ Das KI-Modell konnte nicht geladen werden. Bitte überprüfe keras_model.h5 und labels.txt.")
        st.stop()

    source = st.radio("Bildquelle", ["📷 Kamera", "📁 Bild hochladen"], horizontal=True)
    if source == "📷 Kamera":
        file = st.camera_input("Foto aufnehmen")
    else:
        file = st.file_uploader("Bild auswählen", type=["jpg", "jpeg", "png"])

    if file:
        try:
            preview = Image.open(file).convert("RGB")
            st.image(preview, caption="Ausgewähltes Bild", use_container_width=True)
            if st.button("🔍 Gegenstand erkennen", type="primary", use_container_width=True):
                with st.spinner("🤖 Die KI analysiert den Gegenstand ..."):
                    result = predict_image(preview, model, labels)
                file.seek(0)
                st.session_state["result"] = result
                st.session_state["image_bytes"] = file.getvalue()
        except Exception as error:
            st.error("⚠️ Das Bild konnte nicht verarbeitet werden.")
            st.exception(error)

    if "result" in st.session_state:
        result = st.session_state["result"]
        st.markdown(
            f"""<div class="result-card"><div style="font-size:4rem">{emoji(result["label"])}</div><h2>{result["label"]}</h2><p>KI-Sicherheit: <b>{result["confidence"]*100:.2f}%</b></p></div>""",
            unsafe_allow_html=True,
        )
        st.subheader("📊 Wahrscheinlichkeiten")
        for label, probability in result["probabilities"].items():
            st.write(f"**{emoji(label)} {label}: {probability*100:.2f}%**")
            st.progress(float(max(0, min(1, probability))))

        st.divider()
        st.subheader("📝 Fundstück speichern")
        default = labels.index(result["label"]) if result["label"] in labels else 0
        with st.form("save_form"):
            category = st.selectbox("Fundstück", labels, index=default)
            color = st.text_input("Farbe", placeholder="Zum Beispiel: Blau")
            size = st.selectbox("Größe", ["Unbekannt", "XS", "S", "M", "L", "XL"])
            location = st.selectbox("Fundort", ["Schulhof", "Klassenraum", "Sporthalle", "Mensa", "Flur", "Umkleide", "Sonstiger Ort"])
            found_date = st.date_input("Funddatum", value=date.today())
            description = st.text_area("Zusätzliche Beschreibung", placeholder="Zum Beispiel: Blaue Trinkflasche mit schwarzem Deckel.")
            submitted = st.form_submit_button("💾 Fundstück speichern", type="primary", use_container_width=True)

        if submitted:
            try:
                image_path = save_image(io.BytesIO(st.session_state["image_bytes"]))
                save_item(category, color.strip() or "Unbekannt", size, location,
                          found_date, description.strip(), image_path,
                          result["confidence"])
                st.success("✅ Das Fundstück wurde erfolgreich im digitalen Fundbüro gespeichert.")
                st.session_state.pop("result", None)
                st.session_state.pop("image_bytes", None)
            except Exception as error:
                st.error("⚠️ Das Fundstück konnte nicht gespeichert werden.")
                st.exception(error)

elif page == "🔍 Fundstücke suchen":
    st.header("🔍 Fundstücke suchen")
    items = get_all_items()
    categories = ["Alle"] + sorted({i["kategorie"] for i in items if i["kategorie"]})
    locations = ["Alle"] + sorted({i["fundort"] for i in items if i["fundort"]})
    c1, c2, c3 = st.columns(3)
    with c1: category = st.selectbox("Kategorie", categories)
    with c2: location = st.selectbox("Fundort", locations)
    with c3: status = st.selectbox("Status", ["Alle", "Verfügbar", "Abgeholt"])
    color = st.text_input("Farbe")
    text = st.text_input("Freitextsuche", placeholder="Zum Beispiel: schwarze Federtasche")
    use_date = st.checkbox("Nach Funddatum filtern")
    selected_date = st.date_input("Funddatum", value=date.today()) if use_date else None
    results = search_items(category, color, location, selected_date, text, status)
    st.subheader(f"Gefundene Einträge: {len(results)}")
    if not results:
        st.info("🔎 Keine passenden Fundstücke gefunden.")
    for item in results:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                if item["bildpfad"] and Path(item["bildpfad"]).exists():
                    st.image(item["bildpfad"], use_container_width=True)
                else:
                    st.info("📷 Kein Bild verfügbar")
            with right:
                st.subheader(f"{emoji(item['kategorie'])} {item['kategorie']}")
                st.write(f"**Farbe:** {item['farbe'] or 'Unbekannt'}")
                st.write(f"**Fundort:** {item['fundort']}")
                st.write(f"**Datum:** {item['funddatum']}")
                st.write(f"**Status:** {'🟢' if item['status']=='Verfügbar' else '✅'} {item['status']}")
                if item["beschreibung"]: st.write(item["beschreibung"])

elif page == "📦 Übersicht":
    st.header("📦 Meine Fundstücke / Übersicht")
    stats = get_statistics()
    cols = st.columns(5)
    for col, title, value in zip(cols,
        ["📦 Insgesamt","🟢 Verfügbar","✅ Abgeholt","🥤 Trinkflaschen","🧥 Hoodies"],
        [stats["gesamt"],stats["verfuegbar"],stats["abgeholt"],stats["trinkflaschen"],stats["hoodies"]]):
        col.metric(title, value)
    st.divider()
    items = get_all_items()
    if not items: st.info("📦 Noch keine Fundstücke gespeichert.")
    for item in items:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                if item["bildpfad"] and Path(item["bildpfad"]).exists():
                    st.image(item["bildpfad"], use_container_width=True)
            with right:
                st.subheader(f"{emoji(item['kategorie'])} {item['kategorie']}")
                st.write(f"Fundort: **{item['fundort']}** | Status: **{item['status']}**")
                if item["status"] == "Verfügbar" and st.button("✅ Als abgeholt markieren", key=f"collect_{item['id']}"):
                    update_item_status(item["id"], "Abgeholt")
                    st.rerun()
                if st.button("🗑️ Löschen", key=f"delete_{item['id']}"):
                    st.session_state[f"confirm_{item['id']}"] = True
                if st.session_state.get(f"confirm_{item['id']}"):
                    st.warning("⚠️ Wirklich endgültig löschen?")
                    yes, no = st.columns(2)
                    if yes.button("Ja, löschen", key=f"yes_{item['id']}"):
                        deleted = delete_item(item["id"])
                        if deleted and deleted["bildpfad"]:
                            try: Path(deleted["bildpfad"]).unlink(missing_ok=True)
                            except OSError: pass
                        st.session_state.pop(f"confirm_{item['id']}", None)
                        st.rerun()
                    if no.button("Abbrechen", key=f"no_{item['id']}"):
                        st.session_state.pop(f"confirm_{item['id']}", None)
                        st.rerun()

else:
    st.header("ℹ️ Über KathFundBüro")
    st.markdown("""
### Was ist KathFundBüro?
**KathFundBüro** ist ein digitales Fundbüro für das Katharineum.

Die App verwendet künstliche Intelligenz, um gefundene Gegenstände automatisch zu kategorisieren und übersichtlich zu speichern.

### 🤖 KI
Das Modell wurde mit **Teachable Machine** trainiert. Die KI unterstützt bei der Kategorisierung und kann Fehler machen. Deshalb kann die Kategorie vor dem Speichern manuell geändert werden.

### 🔒 Hinweis
In dieser MVP-Version werden Bilder lokal im Ordner `uploads/` und Informationen in einer SQLite-Datenbank gespeichert. Für einen echten schulweiten Einsatz sollten die Datenschutzregeln der Schule geprüft werden.
""")
