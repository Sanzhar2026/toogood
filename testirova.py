# fix_enum.py
import psycopg2

conn = psycopg2.connect(
    host="dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com",
    port=5432,
    database="toogood_db_a3k0",
    user="toogood_db_a3k0_user",
    password="2tWztMrzy1VCriWHefthkLBK1EOeeYnG",
    sslmode="require"
)

# ✅ Включаем автокоммит после подключения
conn.autocommit = True

cur = conn.cursor()

try:
    # Добавляем новое значение в enum
    cur.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'picked_up'")
    print("✅ Значение 'picked_up' добавлено в enum orderstatus")
    
    # Проверяем
    cur.execute("SELECT enum_range(NULL::orderstatus)")
    result = cur.fetchone()
    print(f"📋 Текущие значения enum: {result[0]}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
finally:
    cur.close()
    conn.close()