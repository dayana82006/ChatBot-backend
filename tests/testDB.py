from app.database.database import get_connection

def test_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        result = cursor.fetchone()
        print("✅ Conectado a la base:", result[0])
        cursor.close()
        conn.close()
    except Exception as e:
        print("❌ Error de conexión:", e)

if __name__ == "__main__":
    test_connection()
