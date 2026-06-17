# add_city_column.py
import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def add_city_column():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("=" * 60)
        print("ДОБАВЛЕНИЕ КОЛОНКИ city В surprise_bags")
        print("=" * 60)
        
        # 1. Проверяем существование колонки
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'surprise_bags' AND column_name = 'city'
        """)
        
        if cur.fetchone():
            print("✅ Колонка city уже существует")
            return
        
        # 2. Добавляем колонку
        print("\n1) Добавляем колонку city...")
        cur.execute("ALTER TABLE surprise_bags ADD COLUMN city VARCHAR(100)")
        print("   ✅ Колонка добавлена")
        
        # 3. Обновляем из поставщиков
        print("\n2) Обновляем city из suppliers...")
        cur.execute("""
            UPDATE surprise_bags 
            SET city = suppliers.city 
            FROM suppliers 
            WHERE surprise_bags.supplier_id = suppliers.id
        """)
        print(f"   ✅ Обновлено {cur.rowcount} записей")
        
        # 4. Проверяем NULL значения
        cur.execute("SELECT COUNT(*) FROM surprise_bags WHERE city IS NULL")
        null_count = cur.fetchone()[0]
        
        if null_count > 0:
            print(f"\n   ⚠️ Найдено {null_count} записей с NULL city")
            print("   Устанавливаем 'Алматы' по умолчанию...")
            cur.execute("UPDATE surprise_bags SET city = 'Алматы' WHERE city IS NULL")
            print(f"   ✅ Обновлено {cur.rowcount} записей")
        
        # 5. Делаем NOT NULL
        print("\n3) Делаем city NOT NULL...")
        cur.execute("ALTER TABLE surprise_bags ALTER COLUMN city SET NOT NULL")
        print("   ✅ NOT NULL установлен")
        
        # 6. Создаем индекс
        print("\n4) Создаем индекс...")
        cur.execute("CREATE INDEX idx_surprise_bags_city ON surprise_bags(city)")
        print("   ✅ Индекс создан")
        
        # 7. Проверяем результат
        print("\n5) Проверка результата:")
        cur.execute("SELECT city, COUNT(*) FROM surprise_bags GROUP BY city")
        print("   Сюрпризы по городам:")
        for row in cur.fetchall():
            print(f"      {row[0]}: {row[1]}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ ГОТОВО!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_city_column()