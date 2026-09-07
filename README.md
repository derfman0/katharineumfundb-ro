# 🔎 KathFundBüro

## Die digitale Fundstück-Erkennung für das Katharineum

KathFundBüro ist eine Streamlit-App für ein digitales Schul-Fundbüro. Fundstücke können fotografiert, mit einem Teachable-Machine-Modell klassifiziert und in einer lokalen SQLite-Datenbank gespeichert werden.

## Funktionen

- 📷 Kamera-Foto oder Bild-Upload
- 🤖 KI-Erkennung mit dem vorhandenen `keras_model.h5`
- 📊 Wahrscheinlichkeiten aller Kategorien
- 📝 Speichern von Farbe, Größe, Fundort, Datum und Beschreibung
- 🔍 Suche und Filter
- 📦 Übersicht und Statistiken
- ✅ Status „Abgeholt“
- 🗑️ Löschen mit Sicherheitsabfrage

## Projektstruktur

```text
kathfundbuero/
├── app.py
├── ai_model.py
├── database.py
├── keras_model.h5
├── labels.txt
├── requirements.txt
├── README.md
├── .gitignore
├── uploads/
└── fundbuero.db
```

`fundbuero.db` wird beim ersten Start automatisch erstellt.

## Voraussetzungen

Empfohlen wird Python **3.10 oder 3.11**.

## Installation

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Danach ist die App normalerweise unter `http://localhost:8501` erreichbar.

## GitHub

1. Erstelle ein neues GitHub-Repository.
2. Lade alle Projektdateien hoch.
3. Achte darauf, dass `app.py`, `ai_model.py`, `database.py`, `keras_model.h5` und `labels.txt` im Hauptordner liegen.

## Streamlit Community Cloud

Die App kann mit Streamlit Community Cloud veröffentlicht werden. Als Hauptdatei wird `app.py` ausgewählt.

### Wichtiger Hinweis

Diese MVP-Version nutzt lokale SQLite- und Bildspeicherung. Bei Cloud-Deployments ist dieser Speicher häufig nicht dauerhaft. Für einen echten langfristigen Schulbetrieb wäre später ein persistenter Speicher nötig.

## KI-Hinweis

Die KI ist ein Hilfsmittel und kann falsche Vorhersagen treffen. Die vorgeschlagene Kategorie kann deshalb vor dem Speichern manuell geändert werden.
