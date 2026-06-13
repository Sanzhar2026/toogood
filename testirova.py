import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Добавляем значение в enum
    cursor.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'picked_up'")
    
    # Удаляем проблемные резервации
    cursor.execute("DELETE FROM temporary_reservations WHERE user_id IS NULL")
    
    conn.commit()
    print("✅ База данных исправлена!")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Ошибка: {e}")