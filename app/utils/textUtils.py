import unicodedata
import re

def normalize_text(text: str) -> str:
    """
    Normaliza un texto para comparar nombres sin importar mayúsculas,
    tildes, espacios extras o caracteres especiales.

    Ejemplo:
        "Café Clásico " → "cafe clasico"
        "CAFÉ clásico"  → "cafe clasico"
    """
    if not text:
        return ""

    # Convertir a minúsculas
    text = text.lower()

    # Eliminar tildes y acentos (por ejemplo, á -> a, ñ -> n)
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")

    # Eliminar caracteres no alfanuméricos (excepto espacios)
    text = re.sub(r"[^a-z0-9\s]", "", text)

    # Eliminar espacios duplicados o al principio/final
    text = re.sub(r"\s+", " ", text).strip()

    return text
