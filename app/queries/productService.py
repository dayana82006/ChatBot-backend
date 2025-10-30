import logging
from app.database import get_connection
from app.utils.textUtils import normalize_text  # asegúrate de haber creado esta utilidad

logger = logging.getLogger(__name__)

def get_producto_by_name(nombre_producto: str):
    """
    Busca un producto por nombre, ignorando tildes y mayúsculas.
    Retorna el id del producto si existe, o None si no lo encuentra.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, nombre FROM productos")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()

    nombre_normalizado = normalize_text(nombre_producto)
    for producto in productos:
        if normalize_text(producto["nombre"]) == nombre_normalizado:
            return producto["id"]

    logger.warning(f"⚠️ Producto no encontrado: '{nombre_producto}'")
    return None
