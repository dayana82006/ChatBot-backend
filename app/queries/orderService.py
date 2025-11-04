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
# 🔹 Recalcular total del pedido (helper)
# =====================================================
def recalculate_order_total(pedido_id: int, conn, cursor):
    """
    Recalcula el total del pedido usando los detalles y actualiza la tabla pedidos.
    Usa la conexión y cursor proporcionados (para mantener atomicidad).
    """
    try:
        cursor.execute("""
            SELECT COALESCE(SUM(cantidad * precio_unitario), 0) AS total
            FROM pedido_detalles
            WHERE pedido_id = %s
        """, (pedido_id,))
        row = cursor.fetchone()
        total = row['total'] if isinstance(row, dict) else (row[0] if row else 0)
        cursor.execute("""
            UPDATE pedidos
            SET total = %s, actualizado_en = %s
            WHERE id = %s
        """, (total, datetime.now(), pedido_id))
        logger.info(f"Total recalculado para pedido {pedido_id}: {total}")
    except Exception as e:
        logger.error(f"Error al recalcular total para pedido {pedido_id}: {e}")
        raise

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
    """
    Agrega o actualiza un detalle de pedido en la tabla pedido_detalles.
    
    Args:
        pedido_id (int): ID del pedido
        producto_id: ID del producto
        cantidad (int): Cantidad del producto
        precio_unitario (float): Precio unitario del producto
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Validación de tipos de datos
        pedido_id = int(pedido_id)
        producto_id = int(producto_id)
        cantidad = int(cantidad)
        precio_unitario = float(precio_unitario)

        # Log para debug
        logger.info(f"Agregando/actualizando detalle: Pedido={pedido_id}, Producto={producto_id}, Cantidad={cantidad}, Precio={precio_unitario}")

        # Verificar si el detalle ya existe
        cursor.execute("""
            SELECT id, cantidad 
            FROM pedido_detalles 
            WHERE pedido_id = %s AND producto_id = %s
        """, (pedido_id, producto_id))
        
        detalle = cursor.fetchone()
        
        if detalle:
            # Actualizar cantidad si el detalle existe
            nueva_cantidad = detalle['cantidad'] + cantidad
            cursor.execute("""
                UPDATE pedido_detalles 
                SET cantidad = %s,
                    precio_unitario = %s
                WHERE id = %s
            """, (nueva_cantidad, precio_unitario, detalle['id']))
            
            logger.info(f"Detalle actualizado: ID={detalle['id']}, Nueva cantidad={nueva_cantidad}")
        else:
            # Insertar nuevo detalle
            cursor.execute("""
                INSERT INTO pedido_detalles 
                (pedido_id, producto_id, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s)
            """, (pedido_id, producto_id, cantidad, precio_unitario))
            
            inserted_id = cursor.lastrowid
            logger.info(f"Nuevo detalle insertado: ID={inserted_id}")
        # Recalcular y actualizar total del pedido (misma conexión para atomicidad)
        recalculate_order_total(pedido_id, conn, cursor)

        # Confirmar cambios
        conn.commit()
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error de validación de datos: {str(e)}")
        conn.rollback()
        raise ValueError(f"Error en los datos: {str(e)}")
    except Exception as e:
        logger.error(f"Error de BD en add_or_update_order_detail: {str(e)}")
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
