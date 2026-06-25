# migrate_categories.py - УДАЛЯЕМ name_ru, name_kz, name_en И ДОБАВЛЯЕМ name

import psycopg2

DATABASE_URL = "postgresql://postgres:YHceVkBwWMtDTXqSbqQhsGrnIxeWlcwz@thomas.proxy.rlwy.net:27717/railway"

def run_migration():
    conn = None
    cur = None
    try:
        print("🔌 Подключение к БД Railway...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("📋 ПРОВЕРКА СТРУКТУРЫ ТАБЛИЦЫ supplier_categories")
        
        # 1. ДОБАВИТЬ КОЛОНКУ name (ЕСЛИ НЕТ)
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'supplier_categories' AND column_name = 'name'
        """)
        if not cur.fetchone():
            print("➕ ДОБАВЛЯЮ КОЛОНКУ name...")
            cur.execute("ALTER TABLE supplier_categories ADD COLUMN name VARCHAR(255)")
            print("✅ КОЛОНКА name ДОБАВЛЕНА")
        else:
            print("✅ КОЛОНКА name УЖЕ СУЩЕСТВУЕТ")
        
        # 2. ЗАПОЛНИТЬ name ИЗ name_ru
        cur.execute("""
            UPDATE supplier_categories 
            SET name = name_ru 
            WHERE name IS NULL AND name_ru IS NOT NULL
        """)
        print(f"✅ ЗАПОЛНЕНО name: {cur.rowcount} СТРОК")
        
        # 3. СДЕЛАТЬ name NOT NULL
        cur.execute("ALTER TABLE supplier_categories ALTER COLUMN name SET NOT NULL")
        print("✅ name SET NOT NULL")
        
        # 4. УДАЛИТЬ name_ru
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'supplier_categories' AND column_name = 'name_ru'
        """)
        if cur.fetchone():
            print("🗑️ УДАЛЯЮ КОЛОНКУ name_ru...")
            cur.execute("ALTER TABLE supplier_categories DROP COLUMN name_ru CASCADE")
            print("✅ КОЛОНКА name_ru УДАЛЕНА")
        
        # 5. УДАЛИТЬ name_kz
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'supplier_categories' AND column_name = 'name_kz'
        """)
        if cur.fetchone():
            print("🗑️ УДАЛЯЮ КОЛОНКУ name_kz...")
            cur.execute("ALTER TABLE supplier_categories DROP COLUMN name_kz CASCADE")
            print("✅ КОЛОНКА name_kz УДАЛЕНА")
        
        # 6. УДАЛИТЬ name_en
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'supplier_categories' AND column_name = 'name_en'
        """)
        if cur.fetchone():
            print("🗑️ УДАЛЯЮ КОЛОНКУ name_en...")
            cur.execute("ALTER TABLE supplier_categories DROP COLUMN name_en CASCADE")
            print("✅ КОЛОНКА name_en УДАЛЕНА")
        
        # 7. ПРОВЕРИТЬ ИТОГ
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'supplier_categories'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        print("")
        print("📋 ИТОГОВАЯ СТРУКТУРА supplier_categories:")
        for col in columns:
            print(f"   - {col[0]}")
        
        conn.commit()
        print("")
        print("✅ ✅ ✅ ВСЕ ИЗМЕНЕНИЯ ПРИМЕНЕНЫ!")
        print("")
        print("📋 ИТОГ:")
        print("   - ДОБАВЛЕНА: name (NOT NULL)")
        print("   - УДАЛЕНЫ: name_ru, name_kz, name_en")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("🔌 Соединение закрыто")

if __name__ == "__main__":
    run_migration()