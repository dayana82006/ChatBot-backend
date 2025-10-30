import logging
from datetime import datetime
from app.database import get_connection
# Asegúrate de que esta importación sea correcta para tu proyecto
from app.queries.productService import get_producto_by_name 

logger = logging.getLogger(__name__)

# =====================================================
# 🔹 Funciones de Soporte
# =====================================================

def delete_order(pedido_id: int):
    """Elimina un pedido (y sus detalles por CASCADE)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
        conn.commit()
        logger.warning(f"🗑️ Pedido {pedido_id} eliminado debido a un fallo en el flujo.")
    except Exception as e:
        logger.error(f"Error al intentar eliminar el pedido {pedido_id}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_last_product_detail(pedido_id: int):
    """Retorna el producto_id, precio_unitario y cantidad del último detalle añadido al pedido."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT producto_id, precio_unitario, cantidad 
            FROM pedido_detalles
            WHERE pedido_id = %s
            ORDER BY id DESC LIMIT 1
        """, (pedido_id,))
        detalle = cursor.fetchone()
        return detalle
    except Exception as e:
        logger.error(f"Error al obtener el último detalle del pedido {pedido_id}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# =====================================================
# 🔹 Obtener o crear pedido pendiente para un usuario
# =====================================================
def get_or_create_pending_order(user_id: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM pedidos 
            WHERE user_id = %s AND estado = 'pendiente'
            ORDER BY id DESC LIMIT 1
        """, (user_id,))
        
        pedido = cursor.fetchone()
        if not pedido:
            cursor.execute("""
                INSERT INTO pedidos (user_id, total, estado)
                VALUES (%s, 0, 'pendiente')
            """, (user_id,))
            conn.commit()
            pedido_id = cursor.lastrowid
            logger.info(f"🆕 Pedido creado para usuario {user_id} (ID: {pedido_id})")
        else:
            pedido_id = pedido["id"]
        
        return pedido_id
    except Exception as e:
        logger.error(f"Error en get_or_create_pending_order: {e}")
        conn.rollback()
        # Se relanza para que el agente maneje el fallo de conexión/BD
        raise
    finally:
        cursor.close()
        conn.close()


# =====================================================
# 🔹 Agregar o actualizar producto en el pedido (CORREGIDO)
# =====================================================
def add_or_update_order_detail(pedido_id: int, producto_id, cantidad: int, precio_unitario: float):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Búsqueda y validación si el producto_id vino como string
        if isinstance(producto_id, str):
            if not producto_id.isdigit():
                producto_real_id = get_producto_by_name(producto_id)
                if not producto_real_id:
                    raise ValueError(f"Producto '{producto_id}' no se encontró en el catálogo.")
                producto_id = producto_real_id
            
        # 2. Conversión a entero y validación final
        try:
            producto_id = int(producto_id)
        except (TypeError, ValueError):
            # Esto maneja casos donde 'producto_id' es None
            raise ValueError(f"ID de producto no válido o nulo: {producto_id}")

        # 🚨 LÍNEA CLAVE DE DEBUG: Muestra el ID final antes de la BD
        logger.debug(f"DEBUG: Insertando/Actualizando Detalle: Pedido ID={pedido_id}, Producto ID={producto_id}, Cantidad={cantidad}")

        # 🟢 Verificar si el detalle ya existe
        cursor.execute("""
            SELECT id, cantidad FROM pedido_detalles
            WHERE pedido_id = %s AND producto_id = %s
        """, (pedido_id, producto_id))
        
        detalle = cursor.fetchone()

        if detalle:
            # Lógica de UPDATE
            nueva_cantidad = detalle[1] + cantidad
            cursor.execute("""
                UPDATE pedido_detalles
                SET cantidad = %s
                WHERE id = %s
            """, (nueva_cantidad, detalle[0]))
        else:
            # Lógica de INSERT (Aquí es donde falla la clave foránea)
            cursor.execute("""
                INSERT INTO pedido_detalles (pedido_id, producto_id, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s)
            """, (pedido_id, producto_id, cantidad, precio_unitario))

        conn.commit()
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error de BD en add_or_update_order_detail: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# =====================================================
# 🔹 Actualizar estado del pedido
# =====================================================
def update_order_status(pedido_id: int, nuevo_estado: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE pedidos 
            SET estado = %s, actualizado_en = %s
            WHERE id = %s
        """, (nuevo_estado, datetime.now(), pedido_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Error al actualizar estado del pedido {pedido_id}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# =====================================================
# 🔹 Obtener resumen del pedido
# =====================================================
def get_order_summary(pedido_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                p.id AS pedido_id,
                p.total,
                p.estado,
                d.producto_id,
                prod.nombre AS producto_nombre,
                d.cantidad,
                d.precio_unitario
            FROM pedidos p
            JOIN pedido_detalles d ON p.id = d.pedido_id
            JOIN productos prod ON d.producto_id = prod.id
            WHERE p.id = %s
        """, (pedido_id,))
        
        detalles = cursor.fetchall()
        return detalles
    except Exception as e:
        logger.error(f"Error al obtener resumen del pedido {pedido_id}: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
