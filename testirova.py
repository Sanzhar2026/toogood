# fix_pickup_orders.py
import psycopg2

conn = psycopg2.connect(
    host="dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com",
    port=5432,
    database="toogood_db_a3k0",
    user="toogood_db_a3k0_user",
    password="2tWztMrzy1VCriWHefthkLBK1EOeeYnG",
    sslmode="require"
)

cur = conn.cursor()

# Проверяем
cur.execute("""
    SELECT id, order_number, delivery_type, status, assigned_courier_id 
    FROM orders 
    WHERE delivery_type = 'pickup'
""")
print("📋 Заказы с самовывозом:")
for row in cur.fetchall():
    print(f"   ID: {row[0]}, №: {row[1]}, статус: {row[3]}, курьер: {row[4]}")

# ✅ ИСПРАВЛЕНО: статус большими буквами 'CONFIRMED'
cur.execute("""
    UPDATE orders 
    SET assigned_courier_id = NULL, status = 'CONFIRMED' 
    WHERE delivery_type = 'pickup' AND assigned_courier_id IS NOT NULL
""")
print(f"\n✅ Обновлено {cur.rowcount} заказов")

conn.commit()
cur.close()
conn.close()