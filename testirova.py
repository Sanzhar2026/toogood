import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com:5432/toogood_db_a3k0?sslmode=require"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Откатываем транзакцию
conn.rollback()

# Добавляем значение
cur.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'picked_up'")
conn.commit()
print("✅ 'picked_up' добавлен в enum БД")

# Проверяем
cur.execute("SELECT unnest(enum_range(NULL::orderstatus))")
values = cur.fetchall()
print("📋 Все значения orderstatus:")
for v in values:
    print(f"   - {v[0]}")

cur.close()
conn.close()