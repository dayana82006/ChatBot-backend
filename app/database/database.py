import mysql.connector
from app.config import settings

def get_connection():
    return mysql.connector.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        port=settings.DB_PORT
    )


def init_db():
    try:
        conn = get_connection()
        conn.close()
        print("✅ Conexión a la base de datos exitosa")
    except Exception as e:
        print("❌ Error al conectar con la base de datos:", e)
        raise e