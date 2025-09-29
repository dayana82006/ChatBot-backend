import mysql.connector
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def get_connection():
    """Obtiene una conexión a la base de datos MySQL"""
    try:
        connection = mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=settings.DB_PORT,
            autocommit=True
        )
        return connection
    except Exception as e:
        logger.error(f"Error al conectar con la base de datos: {e}")
        raise e

def init_db():
    """Inicializa la base de datos y verifica la conexión"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar que las tablas existen
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        logger.info(f"Tablas encontradas: {tables}")
        
        cursor.close()
        conn.close()
        logger.info("✅ Conexión a la base de datos exitosa")
        
    except Exception as e:
        logger.error(f"❌ Error al conectar con la base de datos: {e}")
        raise e

def execute_schema():
    """Ejecuta el schema SQL para crear las tablas"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Crear tablas si no existen
        schema_sql = """
        -- =====================================================
        -- TABLA: users (información adicional)
        -- =====================================================
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) UNIQUE NOT NULL COMMENT 'ID único del usuario',
            name VARCHAR(255) DEFAULT NULL COMMENT 'Nombre del usuario',
            email VARCHAR(255) DEFAULT NULL COMMENT 'Email del usuario',
            phone VARCHAR(50) DEFAULT NULL COMMENT 'Teléfono del usuario',
            channel VARCHAR(50) DEFAULT 'web' COMMENT 'Canal principal del usuario',
            metadata JSON DEFAULT NULL COMMENT 'Información adicional en formato JSON',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de registro',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Última actualización'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Información adicional de usuarios';

        -- =====================================================
        -- TABLA: productos
        -- Almacena los productos disponibles en el sistema
        -- =====================================================
        CREATE TABLE IF NOT EXISTS productos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL COMMENT 'Nombre del producto',
            descripcion TEXT COMMENT 'Descripción del producto',
            categoria VARCHAR(100) COMMENT 'Categoría del producto',
            origen VARCHAR(100) COMMENT 'Origen del producto',
            organico BOOLEAN DEFAULT FALSE COMMENT 'Indica si el producto es orgánico',
            presentacion VARCHAR(100) COMMENT 'Presentación del producto (por ejemplo: 500g, 1kg)',
            precio DECIMAL(10, 2) NOT NULL COMMENT 'Precio del producto',
            moneda VARCHAR(20) DEFAULT 'USD' COMMENT 'Moneda del precio',
            stock INT NOT NULL COMMENT 'Cantidad en stock del producto',
            metadata JSON DEFAULT NULL COMMENT 'Información adicional en formato JSON',
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación del producto',
            actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Última actualización del producto'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Productos disponibles en el sistema';

        -- =====================================================
        -- TABLA: pedidos
        -- Almacena los pedidos realizados por los usuarios
        -- =====================================================
        CREATE TABLE IF NOT EXISTS pedidos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL COMMENT 'ID del usuario que realizó el pedido',
            total DECIMAL(10, 2) NOT NULL COMMENT 'Total del pedido',
            estado VARCHAR(50) DEFAULT 'pendiente' COMMENT 'Estado del pedido (pendiente, procesado, etc.)',
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación del pedido',
            actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Última actualización del pedido',
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Pedidos realizados por los usuarios';

        -- =====================================================
        -- TABLA: pedido_detalles
        -- Almacena los detalles de cada pedido (productos específicos)
        -- =====================================================
        CREATE TABLE IF NOT EXISTS pedido_detalles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pedido_id INT NOT NULL COMMENT 'Referencia al pedido',
            producto_id INT NOT NULL COMMENT 'Referencia al producto',
            cantidad INT NOT NULL COMMENT 'Cantidad del producto en el pedido',
            precio_unitario DECIMAL(10, 2) NOT NULL COMMENT 'Precio unitario del producto en el momento del pedido',
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Detalles de los productos en un pedido';

        -- =====================================================
        -- TABLA: chats
        -- Almacena las conversaciones de usuarios por canal
        -- =====================================================
        CREATE TABLE IF NOT EXISTS chats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL COMMENT 'ID del usuario (número WhatsApp, user_id web, etc.)',
            channel VARCHAR(50) DEFAULT 'web' COMMENT 'Canal de comunicación: web, whatsapp, telegram',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación del chat',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Última actualización',
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Conversaciones de usuarios por canal';

        -- =====================================================
        -- TABLA: messages
        -- Almacena todos los mensajes de las conversaciones
        -- =====================================================
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            chat_id INT NOT NULL COMMENT 'Referencia al chat',
            role VARCHAR(50) NOT NULL COMMENT 'Rol del mensaje: user o assistant',
            text TEXT NOT NULL COMMENT 'Contenido del mensaje',
            `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento del mensaje',
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mensajes de las conversaciones';
        """
        
        # Ejecutar el schema SQL
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        cursor.close()
        conn.close()
        logger.info("✅ Schema de base de datos ejecutado correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando schema: {e}")
        raise e
