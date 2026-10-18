from database import get_db_connection

conn = None
cursor= None

try:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1")
    result = cursor.fetchone()

    print("✅ Connected to database successfully:", result)

except Exception as e:
    print("❌ Error:", e)
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()