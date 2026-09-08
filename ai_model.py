from pathlib import Path
from functools import lru_cache

import numpy as np
from PIL import Image
import tensorflow as tf


# --------------------------------------------------
# DATEIPFADE
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "keras_model.h5"
LABELS_PATH = BASE_DIR / "labels.txt"


# --------------------------------------------------
# LABELS LADEN
# --------------------------------------------------

@lru_cache(maxsize=1)
def load_labels():
    """
    Lädt die Kategorien automatisch aus labels.txt.
    Unterstützt das Teachable-Machine-Format:
    0 Kurzehose
    1 Trinkflasche
    usw.
    """

    if not LABELS_PATH.exists():
        raise FileNotFoundError(
            f"labels.txt wurde nicht gefunden: {LABELS_PATH}"
        )

    labels = []

    with open(LABELS_PATH, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            parts = line.split(maxsplit=1)

            # Beispiel: "0 Hoodie" → "Hoodie"
            if len(parts) == 2 and parts[0].isdigit():
                label = parts[1].strip()
            else:
                label = line

            labels.append(label)

    if not labels:
        raise ValueError("labels.txt enthält keine Kategorien.")

    return labels


# --------------------------------------------------
# MODELL LADEN
# --------------------------------------------------

@lru_cache(maxsize=1)
def load_model():
    """
    Lädt das Teachable-Machine-Modell nur einmal.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"keras_model.h5 wurde nicht gefunden: {MODEL_PATH}"
        )

    if MODEL_PATH.stat().st_size == 0:
        raise ValueError(
            "Die Datei keras_model.h5 ist leer."
        )

    try:
        model = tf.keras.models.load_model(
            str(MODEL_PATH),
            compile=False
        )

        return model

    except Exception as error:
        raise RuntimeError(
            "Das KI-Modell konnte nicht geladen werden.\n"
            f"Technischer Fehler: {error}"
        )


# --------------------------------------------------
# BILD VORBEREITEN
# --------------------------------------------------

def prepare_image(image):
    """
    Bereitet ein Bild für Teachable Machine vor.

    Das Modell erwartet:
    - RGB
    - 224 x 224 Pixel
    - float32
    - Normalisierung von -1 bis 1
    """

    if not isinstance(image, Image.Image):
        raise TypeError(
            "Das Bild konnte nicht verarbeitet werden."
        )

    # RGB
    image = image.convert("RGB")

    # Größe
    image = image.resize((224, 224))

    # NumPy Array
    image_array = np.asarray(
        image,
        dtype=np.float32
    )

    # Teachable-Machine-Normalisierung
    image_array = (
        image_array / 127.5
    ) - 1

    # Batch-Dimension
    image_array = np.expand_dims(
        image_array,
        axis=0
    )

    return image_array


# --------------------------------------------------
# KI-VORHERSAGE
# --------------------------------------------------

def predict_image(image):
    """
    Analysiert ein Bild.

    Diese Funktion benötigt NUR das Bild:

    result = predict_image(image)

    Rückgabe:
    {
        "label": "Hoodie",
        "confidence": 0.95,
        "probabilities": {...}
    }
    """

    model = load_model()
    labels = load_labels()

    prepared_image = prepare_image(image)

    prediction = model.predict(
        prepared_image,
        verbose=0
    )

    prediction = np.asarray(prediction)

    # Batch-Dimension entfernen
    if prediction.ndim == 2:
        prediction = prediction[0]

    # Überprüfen
    if prediction.ndim != 1:
        raise ValueError(
            f"Unerwartete Modellausgabe: {prediction.shape}"
        )

    if len(prediction) != len(labels):
        raise ValueError(
            "Die Anzahl der Modell-Ergebnisse passt "
            "nicht zu den Kategorien in labels.txt."
        )

    # Höchste Wahrscheinlichkeit
    best_index = int(np.argmax(prediction))

    best_label = labels[best_index]
    confidence = float(prediction[best_index])

    probabilities = {}

    for label, probability in zip(labels, prediction):
        probabilities[label] = float(probability)

    return {
        "label": best_label,
        "confidence": confidence,
        "probabilities": probabilities
    }
