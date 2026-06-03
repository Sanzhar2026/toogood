# update_enum.py
import psycopg2
import os

# Данные для подключения (из Render)
DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

def update_enum():
    try:
        # Подключаемся к БД
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Добавляем значение 'nearby' в enum orderstatus
        cursor.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'nearby';")
        print("✅ Значение 'nearby' добавлено в enum orderstatus")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    update_enum()