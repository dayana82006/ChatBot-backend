import logging
from app.database.database import get_connection
from app.services.qdrant_service import get_all_products

def sync_products_from_qdrant():
    """
    Sincroniza los productos almacenados en Qdrant con la base de datos MySQL.
    """
    logging.info("🔄 Iniciando sincronización de productos desde Qdrant...")

    productos = get_all_products()
    if not productos:
        logging.warning("⚠️ No se encontraron productos en Qdrant.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    for p in productos:
        # Mapeo flexible según los datos que vienen de Qdrant
        nombre = p.get("nombre") or p.get("title") or "Producto sin nombre"
        descripcion = p.get("descripcion") or p.get("description") or ""
        categoria = p.get("categoria") or "General"
        origen = p.get("origen") or "Desconocido"
        organico = bool(p.get("organico") or False)
        presentacion = p.get("presentacion") or "Unidad"
        precio = float(p.get("precio") or p.get("price") or 0.00)
        moneda = p.get("moneda") or "USD"
        stock = int(p.get("stock") or 0)
        metadata = str(p.get("metadata") or "{}")

        # Insertar solo si no existe (por nombre)
        cursor.execute("""
            SELECT COUNT(*) FROM productos WHERE nombre = %s
        """, (nombre,))
        existe = cursor.fetchone()[0]

        if not existe:
            cursor.execute("""
                INSERT INTO productos (
                    nombre, descripcion, categoria, origen, organico,
                    presentacion, precio, moneda, stock, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nombre, descripcion, categoria, origen, organico,
                presentacion, precio, moneda, stock, metadata
            ))

    conn.commit()
    cursor.close()
    conn.close()

    logging.info(f"✅ Sincronizados {len(productos)} productos desde Qdrant a MySQL.")

if __name__ == "__main__":
    print("✅ Sincronización de productos completada.")
