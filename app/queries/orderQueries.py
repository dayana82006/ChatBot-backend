from app.database.database import get_connection
from typing import Dict, Any, List
import logging
import json

logger = logging.getLogger(__name__)

def create_order(user_id: str, total: float, shipping_data: Dict[str, Any], payment_method: str) -> int:
    """Crea un nuevo pedido en la base de datos"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Primero asegurarnos de que el usuario existe
        cursor.execute(
            "INSERT IGNORE INTO users (user_id, channel) VALUES (%s, 'web')",
            (user_id,)
        )
        
        # Crear el pedido
        cursor.execute(
            "INSERT INTO pedidos (user_id, total) VALUES (%s, %s)",
            (user_id, total)
        )
        order_id = cursor.lastrowid
        
        # Actualizar información del usuario si hay datos de envío
        if shipping_data:
            cursor.execute(
                """UPDATE users 
                   SET name = %s, phone = %s, metadata = JSON_OBJECT('address', %s, 'city', %s)
                   WHERE user_id = %s""",
                (
                    shipping_data.get('name'),
                    shipping_data.get('phone'),
                    shipping_data.get('address'),
                    shipping_data.get('city'),
                    user_id
                )
            )
        
        logger.info(f"✅ Pedido creado: ID={order_id}, user_id={user_id}, total={total}")
        return order_id
    except Exception as e:
        logger.error(f"❌ Error creando pedido: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def create_order_detail(order_id: int, product_name: str, quantity: int, unit_price: float, grind_type: str = None):
    """Crea un detalle de pedido"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Primero obtener el product_id basado en el nombre
        cursor.execute(
            "SELECT id FROM productos WHERE nombre LIKE %s LIMIT 1",
            (f"%{product_name}%",)
        )
        product_result = cursor.fetchone()
        
        if product_result:
            product_id = product_result[0]
            
            # Insertar detalle del pedido SIN metadata
            cursor.execute(
                """INSERT INTO pedido_detalles 
                   (pedido_id, producto_id, cantidad, precio_unitario) 
                   VALUES (%s, %s, %s, %s)""",
                (order_id, product_id, quantity, unit_price)
            )
            
            logger.info(f"✅ Detalle de pedido creado: order_id={order_id}, product={product_name}, quantity={quantity}")
        else:
            # Si no encontramos el producto, lo insertamos como un producto nuevo
            cursor.execute(
                "INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s)",
                (product_name, unit_price, 0)
            )
            product_id = cursor.lastrowid
            
            cursor.execute(
                """INSERT INTO pedido_detalles 
                   (pedido_id, producto_id, cantidad, precio_unitario) 
                   VALUES (%s, %s, %s, %s)""",
                (order_id, product_id, quantity, unit_price)
            )
            
            logger.info(f"✅ Producto nuevo y detalle creados: {product_name}")
            
    except Exception as e:
        logger.error(f"❌ Error creando detalle de pedido: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def get_orders_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Obtiene todos los pedidos de un usuario"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # QUERY ACTUALIZADA: Sin la columna metadata
        cursor.execute(
            """SELECT p.*, pd.cantidad, pd.precio_unitario, pr.nombre as producto_nombre
               FROM pedidos p
               LEFT JOIN pedido_detalles pd ON p.id = pd.pedido_id
               LEFT JOIN productos pr ON pd.producto_id = pr.id
               WHERE p.user_id = %s
               ORDER BY p.creado_en DESC""",
            (user_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"❌ Error obteniendo órdenes: {e}")
        return []
    finally:
        cursor.close()
        conn.close()