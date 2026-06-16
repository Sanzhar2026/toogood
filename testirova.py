# fix_lowercase_final.py
import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def fix_to_lowercase():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("=" * 60)
        print("🔄 ПЕРЕВОД СТАТУСОВ В LOWERcase")
        print("=" * 60)
        
        # 1. Сначала меняем тип колонки на VARCHAR
        print("\n1️⃣ Меняем тип колонки на VARCHAR...")
        cur.execute("ALTER TABLE orders ALTER COLUMN status TYPE VARCHAR(50)")
        print("   ✅ Теперь VARCHAR")
        
        # 2. Обновляем статусы на lowercase
        print("\n2️⃣ Обновляем статусы на lowercase...")
        cur.execute("UPDATE orders SET status = LOWER(status)")
        print(f"   ✅ Обновлено {cur.rowcount} записей")
        
        # 3. Проверяем текущие статусы
        print("\n3️⃣ Текущие статусы:")
        cur.execute("SELECT DISTINCT status FROM orders")
        for row in cur.fetchall():
            print(f"   • {row[0]}")
        
        # 4. Удаляем старый enum
        print("\n4️⃣ Удаление старого enum...")
        cur.execute("DROP TYPE IF EXISTS orderstatus CASCADE")
        print("   ✅ Старый enum удален")
        
        # 5. Создаем новый enum с lowercase
        print("\n5️⃣ Создание нового enum...")
        cur.execute("""
            CREATE TYPE orderstatus AS ENUM (
                'pending', 'confirmed', 'preparing', 
                'ready_for_pickup', 'picked_up', 
                'out_for_delivery', 'nearby', 'delivered', 'cancelled'
            )
        """)
        print("   ✅ Новый enum создан")
        
        # 6. Конвертируем обратно в enum
        print("\n6️⃣ Конвертация в enum...")
        cur.execute("ALTER TABLE orders ALTER COLUMN status TYPE orderstatus USING status::orderstatus")
        print("   ✅ Колонка конвертирована в enum")
        
        # 7. Устанавливаем DEFAULT
        print("\n7️⃣ Установка DEFAULT...")
        cur.execute("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'pending'")
        print("   ✅ DEFAULT установлен")
        
        # 8. Проверяем финальный результат
        print("\n8️⃣ Финальная проверка:")
        cur.execute("SELECT enum_range(NULL::orderstatus)")
        print(f"   Enum values: {cur.fetchone()[0]}")
        
        cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        print("\n   Статусы заказов:")
        for row in cur.fetchall():
            print(f"      • {row[0]}: {row[1]} заказов")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ ГОТОВО! Теперь все статусы в lowercase!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_to_lowercase()