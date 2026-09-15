import torch
from PIL import Image
from functools import lru_cache
from transformers import pipeline


# ============================================================
# KATHFUNDBÜRO - KI-KATEGORIEN
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


# Englische Begriffe helfen CLIP teilweise,
# weil das Modell stark mit englischen Bild-Text-Beziehungen
# trainiert wurde.
CATEGORY_PROMPTS = {
    "Trinkflasche": "a photo of a water bottle",
    "Brotdose": "a photo of a lunch box",
    "Federtasche": "a photo of a pencil case",
    "Bleistift": "a photo of a pencil",
    "Kugelschreiber": "a photo of a ballpoint pen",
    "Füller": "a photo of a fountain pen",
    "Textmarker": "a photo of a highlighter pen",
    "Filzstift": "a photo of a felt tip pen",
    "Buntstift": "a photo of a colored pencil",
    "Radiergummi": "a photo of an eraser",
    "Spitzer": "a photo of a pencil sharpener",
    "Lineal": "a photo of a ruler",
    "Geodreieck": "a photo of a set square",
    "Zirkel": "a photo of a compass for drawing",
    "Schere": "a photo of scissors",
    "Klebestift": "a photo of a glue stick",
    "Notizbuch": "a photo of a notebook",
    "Collegeblock": "a photo of a spiral notebook",
    "Hausaufgabenheft": "a photo of a school planner",
    "Mappe": "a photo of a document folder",
    "Ordner": "a photo of a school binder",
    "Schnellhefter": "a photo of a plastic school folder",
    "Buch": "a photo of a book",
    "Schulbuch": "a photo of a school textbook",
    "Taschenrechner": "a photo of a calculator",
    "Handy": "a photo of a smartphone",
    "Kopfhörer": "a photo of headphones",
    "Ladekabel": "a photo of a charging cable",
    "Powerbank": "a photo of a power bank",
    "USB-Stick": "a photo of a USB flash drive",
    "Schlüssel": "a photo of keys",
    "Portemonnaie": "a photo of a wallet",
    "Brille": "a photo of eyeglasses",
    "Sonnenbrille": "a photo of sunglasses",
    "Regenschirm": "a photo of an umbrella",
    "Fahrradhelm": "a photo of a bicycle helmet",
    "Rucksack": "a photo of a backpack",
    "Sporttasche": "a photo of a sports bag",
    "Turnbeutel": "a photo of a gym drawstring bag",
    "Jacke": "a photo of a jacket",
    "Hoodie": "a photo of a hoodie",
    "Pullover": "a photo of a sweater",
    "T-Shirt": "a photo of a t-shirt",
    "Hose": "a photo of trousers",
    "Kurze Hose": "a photo of shorts",
    "Schuhe": "a photo of shoes",
    "Mütze": "a photo of a beanie",
    "Schal": "a photo of a scarf",
    "Handschuhe": "a photo of gloves",
    "Sonstiger Gegenstand": "a photo of another everyday object",
}


MODEL_NAME = "openai/clip-vit-base-patch32"


@lru_cache(maxsize=1)
def get_classifier():
    """
    Lädt das Hugging-Face-Modell nur einmal.
    Danach wird es im Streamlit-Prozess wiederverwendet.
    """

    device = 0 if torch.cuda.is_available() else -1

    classifier = pipeline(
        task="zero-shot-image-classification",
        model=MODEL_NAME,
        device=device
    )

    return classifier


def predict_image(image: Image.Image):
    """
    Erkennt einen Gegenstand auf einem Bild.

    Rückgabe:
        label       = erkannte Kategorie
        confidence  = Wahrscheinlichkeit
        results     = Top-Ergebnisse
    """

    if image is None:
        raise ValueError("Kein Bild wurde übergeben.")

    if not isinstance(image, Image.Image):
        image = Image.open(image)

    image = image.convert("RGB")

    classifier = get_classifier()

    candidate_labels = [
        CATEGORY_PROMPTS[category]
        for category in CATEGORIES
    ]

    results = classifier(
        image,
        candidate_labels=candidate_labels
    )

    # Übersetzung Prompt -> deutsche Kategorie
    prompt_to_category = {
        prompt: category
        for category, prompt in CATEGORY_PROMPTS.items()
    }

    converted_results = []

    for result in results:
        prompt = result["label"]

        category = prompt_to_category.get(
            prompt,
            "Sonstiger Gegenstand"
        )

        converted_results.append({
            "label": category,
            "score": float(result["score"])
        })

    # Höchste Wahrscheinlichkeit zuerst
    converted_results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    best = converted_results[0]

    return (
        best["label"],
        best["score"],
        converted_results[:5]
    )
