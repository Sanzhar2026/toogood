# update_db_columns.py
from sqlalchemy import create_engine, text

# Используй ПРАВИЛЬНУЮ строку подключения к Render
DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP;"))
        conn.commit()
        print("✅ Добавлена колонка cancelled_at")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
    
    try:
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_type VARCHAR(50) DEFAULT 'delivery';"))
        conn.commit()
        print("✅ Добавлена колонка delivery_type")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
    
    # Проверка
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'orders' AND column_name IN ('cancelled_at', 'delivery_type');"))
    print("Колонки в таблице orders:", [row[0] for row in result])