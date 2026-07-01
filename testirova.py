# create_templates_table.py
import psycopg2

DATABASE_URL = "postgresql://postgres:YHceVkBwWMtDTXqSbqQhsGrnIxeWlcwz@thomas.proxy.rlwy.net:27717/railway"

def migrate_database():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("🔄 Начинаем миграцию...")
    
    # ============================================================
    # 1. ПЕРЕИМЕНОВЫВАЕМ КОЛОНКИ В ТАБЛИЦЕ suppliers
    # ============================================================
    try:
        # Проверяем, существует ли колонка pickup_start_time
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='suppliers' AND column_name='pickup_start_time'
        """)
        if cur.fetchone():
            cur.execute("ALTER TABLE suppliers RENAME COLUMN pickup_start_time TO opening_time")
            print("✅ pickup_start_time → opening_time")
        else:
            print("ℹ️ Колонка pickup_start_time не найдена, пропускаем")
            
        # Проверяем, существует ли колонка pickup_end_time
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='suppliers' AND column_name='pickup_end_time'
        """)
        if cur.fetchone():
            cur.execute("ALTER TABLE suppliers RENAME COLUMN pickup_end_time TO closing_time")
            print("✅ pickup_end_time → closing_time")
        else:
            print("ℹ️ Колонка pickup_end_time не найдена, пропускаем")
            
    except Exception as e:
        print(f"⚠️ Ошибка при переименовании: {e}")
    
    # ============================================================
    # 2. СОЗДАЕМ ТАБЛИЦУ supplier_templates
    # ============================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS supplier_templates (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            template_data TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    print("✅ Таблица supplier_templates создана!")
    
    # ============================================================
    # 3. ПРОВЕРЯЕМ, ЧТО ВСЕ ОК
    # ============================================================
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='suppliers' 
        AND column_name IN ('opening_time', 'closing_time')
    """)
    columns = cur.fetchall()
    print(f"📋 Колонки в suppliers: {[c[0] for c in columns]}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("✅ Миграция завершена успешно!")

if __name__ == "__main__":
    migrate_database()