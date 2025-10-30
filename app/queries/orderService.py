import logging
from datetime import datetime
from app.database import get_connection

logger = logging.getLogger(__name__)

# =====================================================
# 🔹 Obtener o crear pedido pendiente para un usuario
# =====================================================
def get_or_create_pending_order(user_id: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
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
    
    cursor.close()
    conn.close()
    return pedido_id

# =====================================================
# 🔹 Agregar o actualizar producto en el pedido
# =====================================================
def add_or_update_order_detail(pedido_id: int, producto_id, cantidad: int, precio_unitario: float):
    conn = get_connection()
    cursor = conn.cursor()

    # 🟡 Si el producto_id viene como texto, buscar el id real
    if isinstance(producto_id, str):
        cursor.execute("""
            SELECT id FROM productos 
            WHERE LOWER(nombre) = LOWER(%s)
        """, (producto_id.strip(),))
        result = cursor.fetchone()
        if not result:
            print(f"⚠️ Producto no encontrado: '{producto_id}'")
            cursor.close()
            conn.close()
            return
        producto_id = result[0]

    # 🟢 Verificar si el detalle ya existe
    cursor.execute("""
        SELECT id, cantidad FROM pedido_detalles
        WHERE pedido_id = %s AND producto_id = %s
    """, (pedido_id, producto_id))
    
    detalle = cursor.fetchone()

    if detalle:
        nueva_cantidad = detalle[1] + cantidad
        cursor.execute("""
            UPDATE pedido_detalles
            SET cantidad = %s
            WHERE id = %s
        """, (nueva_cantidad, detalle[0]))
    else:
        cursor.execute("""
            INSERT INTO pedido_detalles (pedido_id, producto_id, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s)
        """, (pedido_id, producto_id, cantidad, precio_unitario))

    conn.commit()
    cursor.close()
    conn.close()

# =====================================================
# 🔹 Actualizar estado del pedido
# =====================================================
def update_order_status(pedido_id: int, nuevo_estado: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE pedidos 
        SET estado = %s, actualizado_en = %s
        WHERE id = %s
    """, (nuevo_estado, datetime.now(), pedido_id))
    conn.commit()
    cursor.close()
    conn.close()

# =====================================================
# 🔹 Obtener resumen del pedido
# =====================================================
def get_order_summary(pedido_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.id, p.total, p.estado, d.producto_id, d.cantidad, d.precio_unitario
        FROM pedidos p
        JOIN pedido_detalles d ON p.id = d.pedido_id
        WHERE p.id = %s
    """, (pedido_id,))
    
    detalles = cursor.fetchall()
    cursor.close()
    conn.close()
    return detalles
