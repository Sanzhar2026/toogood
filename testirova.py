# add_column_now.py
import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("Добавляем колонку hide_contents...")
    cur.execute("""
        ALTER TABLE surprise_bags 
        ADD COLUMN IF NOT EXISTS hide_contents BOOLEAN DEFAULT FALSE
    """)
    
    print("Создаем индекс...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_surprise_bags_hide_contents 
        ON surprise_bags(hide_contents)
    """)
    
    conn.commit()
    print("✅ Готово! Колонка добавлена.")
    
    # Проверка
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'surprise_bags' AND column_name = 'hide_contents'
    """)
    result = cur.fetchone()
    if result:
        print(f"   Колонка: {result[0]} ({result[1]})")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка: {e}")