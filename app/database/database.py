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
        CREATE TABLE IF NOT EXISTS chats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            channel VARCHAR(50) DEFAULT 'web',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_channel (channel)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            chat_id INT NOT NULL,
            role VARCHAR(50) NOT NULL,
            text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
            INDEX idx_chat_id (chat_id),
            INDEX idx_role (role)
        );
        """
        
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        cursor.close()
        conn.close()
        logger.info("✅ Schema de base de datos ejecutado correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando schema: {e}")
        raise e