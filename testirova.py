# create_viewed_suppliers_table.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = "postgresql://postgres:YHceVkBwWMtDTXqSbqQhsGrnIxeWlcwz@thomas.proxy.rlwy.net:27717/railway"

def create_viewed_suppliers_table():
    """Создать таблицу viewed_suppliers для отслеживания просмотренных поставщиков"""
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("🔄 Создание таблицы viewed_suppliers...")
        
        # ✅ СОЗДАЕМ ТАБЛИЦУ
        cur.execute("""
            CREATE TABLE IF NOT EXISTS viewed_suppliers (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
                viewed_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, supplier_id)
            )
        """)
        print("✅ Таблица viewed_suppliers создана")
        
        # ✅ СОЗДАЕМ ИНДЕКСЫ
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_viewed_suppliers_user_id 
            ON viewed_suppliers(user_id)
        """)
        print("✅ Индекс idx_viewed_suppliers_user_id создан")
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_viewed_suppliers_supplier_id 
            ON viewed_suppliers(supplier_id)
        """)
        print("✅ Индекс idx_viewed_suppliers_supplier_id создан")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ Все готово!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_viewed_suppliers_table()