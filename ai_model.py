from pathlib import Path
import numpy as np
from PIL import Image
import tensorflow as tf

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "keras_model.h5"
LABELS_PATH = BASE_DIR / "labels.txt"

def load_labels(labels_path=LABELS_PATH):
    path = Path(labels_path)
    if not path.exists():
        raise FileNotFoundError(f"labels.txt fehlt: {path}")
    labels = {}
    with path.open(encoding="utf-8") as f:
        for fallback, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2 and parts[0].isdigit():
                labels[int(parts[0])] = parts[1].strip()
            else:
                labels[fallback] = line
    if not labels:
        raise ValueError("labels.txt enthält keine Klassen.")
    return [labels[i] for i in sorted(labels)]

def load_model(model_path=MODEL_PATH):
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"keras_model.h5 fehlt: {path}")
    return tf.keras.models.load_model(path, compile=False)

def prepare_image(image):
    if not isinstance(image, Image.Image):
        image = Image.open(image)
    image = image.convert("RGB").resize((224, 224))
    array = np.asarray(image, dtype=np.float32)
    array = (array / 127.5) - 1.0
    return np.expand_dims(array, axis=0)

def predict_image(image, model, labels=None):
    if labels is None:
        labels = load_labels()
    raw = np.asarray(model.predict(prepare_image(image), verbose=0)[0], dtype=np.float32).flatten()
    if len(raw) != len(labels):
        raise ValueError("Anzahl der Modell-Ausgaben passt nicht zu labels.txt.")
    if np.all(raw >= 0) and raw.sum() > 0:
        probabilities = raw / raw.sum()
    else:
        values = np.exp(raw - np.max(raw))
        probabilities = values / values.sum()
    index = int(np.argmax(probabilities))
    return {
        "label": labels[index],
        "confidence": float(probabilities[index]),
        "probabilities": {labels[i]: float(probabilities[i]) for i in range(len(labels))}
    }
