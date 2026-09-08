from pathlib import Path
import traceback
import sys

import numpy as np
from PIL import Image


# -------------------------------------------------
# PROJEKTPFADE
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "keras_model.h5"
LABELS_PATH = BASE_DIR / "labels.txt"


# TensorFlow wird sicher importiert.
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
    TENSORFLOW_ERROR = None

except Exception as error:
    tf = None
    TENSORFLOW_AVAILABLE = False
    TENSORFLOW_ERROR = str(error)


# -------------------------------------------------
# LABELS LADEN
# -------------------------------------------------

def load_labels():
    """
    Liest die Kategorien automatisch aus labels.txt.

    Teachable Machine verwendet beispielsweise:

    0 Kurzehose
    1 Trinkflasche
    2 Federtasche
    3 Hoodie
    """

    if not LABELS_PATH.exists():
        raise FileNotFoundError(
            f"Die Datei labels.txt wurde nicht gefunden: {LABELS_PATH}"
        )

    if LABELS_PATH.stat().st_size == 0:
        raise ValueError("Die Datei labels.txt ist leer.")

    labels = []

    with open(LABELS_PATH, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            # Teachable-Machine-Format:
            # "0 Kurzehose"
            parts = line.split(maxsplit=1)

            if len(parts) == 2 and parts[0].isdigit():
                label = parts[1].strip()
            else:
                label = line

            if label:
                labels.append(label)

    if not labels:
        raise ValueError(
            "Es konnten keine gültigen Kategorien aus labels.txt gelesen werden."
        )

    return labels


# -------------------------------------------------
# MODELL LADEN
# -------------------------------------------------

def load_model():
    """
    Lädt das Teachable-Machine-Keras-Modell.
    """

    if not TENSORFLOW_AVAILABLE:
        raise ImportError(
            "TensorFlow konnte nicht geladen werden: "
            f"{TENSORFLOW_ERROR}"
        )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Die Modelldatei wurde nicht gefunden: {MODEL_PATH}"
        )

    if MODEL_PATH.stat().st_size == 0:
        raise ValueError(
            "Die Modelldatei keras_model.h5 ist leer."
        )

    try:

        model = tf.keras.models.load_model(
            str(MODEL_PATH),
            compile=False
        )

        return model

    except Exception as error:

        raise RuntimeError(
            f"Das Keras-Modell konnte nicht geladen werden: {error}"
        )


# -------------------------------------------------
# KI-STATUS
# -------------------------------------------------

def get_model_status():
    """
    Prüft, ob das Modell und die Labels verfügbar sind.

    Die Funktion gibt technische Details zurück,
    damit Fehler auf Streamlit Community Cloud
    besser gefunden werden können.
    """

    details = {
        "Python-Version": sys.version,
        "TensorFlow verfügbar": TENSORFLOW_AVAILABLE,
        "Modelldatei": str(MODEL_PATH),
        "Modelldatei vorhanden": MODEL_PATH.exists(),
        "Labels-Datei": str(LABELS_PATH),
        "Labels-Datei vorhanden": LABELS_PATH.exists()
    }

    if TENSORFLOW_AVAILABLE:
        details["TensorFlow-Version"] = tf.__version__

    if MODEL_PATH.exists():
        details["Modelldatei Größe"] = (
            f"{MODEL_PATH.stat().st_size} Bytes"
        )

    try:

        labels = load_labels()

        details["Anzahl Labels"] = len(labels)
        details["Labels"] = labels

    except Exception as error:

        return {
            "available": False,
            "message": (
                "Die Labels konnten nicht geladen werden."
            ),
            "error": str(error),
            "details": details
        }

    try:

        model = load_model()

        details["Modell Eingabe"] = str(model.input_shape)
        details["Modell Ausgabe"] = str(model.output_shape)

        # Prüfen, ob die Anzahl der Klassen passt
        output_shape = model.output_shape

        if isinstance(output_shape, list):
            output_shape = output_shape[0]

        output_classes = output_shape[-1]

        if output_classes != len(labels):

            return {
                "available": False,
                "message": (
                    "Die Anzahl der KI-Kategorien passt "
                    "nicht zu labels.txt."
                ),
                "error": (
                    f"Modell: {output_classes} Klassen, "
                    f"Labels: {len(labels)}"
                ),
                "details": details
            }

        return {
            "available": True,
            "message": (
                "Das KI-Modell wurde erfolgreich geladen."
            ),
            "error": None,
            "details": details
        }

    except Exception as error:

        return {
            "available": False,
            "message": (
                "Das KI-Modell konnte nicht geladen werden."
            ),
            "error": str(error),
            "details": details
        }


# -------------------------------------------------
# BILD VORBEREITEN
# -------------------------------------------------

def prepare_image(image):
    """
    Bereitet ein Bild für das Teachable-Machine-Modell vor.

    Schritte:

    1. RGB
    2. Größe 224 x 224
    3. NumPy Array
    4. float32
    5. Normalisierung auf -1 bis 1
    6. Batch-Dimension
    """

    if not isinstance(image, Image.Image):
        raise TypeError(
            "Das übergebene Objekt ist kein gültiges Bild."
        )

    # RGB
    image = image.convert("RGB")

    # Teachable-Machine-Größe
    image = image.resize((224, 224))

    # NumPy-Array
    image_array = np.asarray(
        image,
        dtype=np.float32
    )

    # Teachable-Machine-Normalisierung
    normalized_image = (
        image_array / 127.5
    ) - 1

    # Batch-Dimension
    data = np.expand_dims(
        normalized_image,
        axis=0
    )

    return data


# -------------------------------------------------
# BILD ERKENNEN
# -------------------------------------------------

def predict_image(image):
    """
    Führt eine KI-Vorhersage durch.

    Rückgabe:

    {
        "label": "...",
        "confidence": 0.95,
        "probabilities": {
            ...
        }
    }
    """

    labels = load_labels()
    model = load_model()

    # Bild vorbereiten
    prepared_image = prepare_image(image)

    # Vorhersage
    prediction = model.predict(
        prepared_image,
        verbose=0
    )

    # NumPy Array
    prediction = np.asarray(prediction)

    # Batch-Dimension entfernen
    if prediction.ndim == 2:

        if prediction.shape[0] != 1:
            raise ValueError(
                "Das Modell hat eine unerwartete "
                "Batch-Ausgabe geliefert."
            )

        prediction = prediction[0]

    if prediction.ndim != 1:
        raise ValueError(
            f"Unerwartete Modell-Ausgabe: {prediction.shape}"
        )

    # Anzahl überprüfen
    if len(prediction) != len(labels):

        raise ValueError(
            f"Anzahl Modellwerte ({len(prediction)}) "
            f"passt nicht zu Anzahl Labels ({len(labels)})."
        )

    # NaN-Werte überprüfen
    if np.any(np.isnan(prediction)):

        raise ValueError(
            "Das KI-Modell hat ungültige NaN-Werte geliefert."
        )

    # Größte Wahrscheinlichkeit
    index = int(np.argmax(prediction))

    predicted_label = labels[index]
    confidence = float(prediction[index])

    probabilities = {}

    for label, probability in zip(labels, prediction):

        probabilities[label] = float(probability)

    return {
        "label": predicted_label,
        "confidence": confidence,
        "probabilities": probabilities
    }
