import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com:5432/toogood_db_a3k0?sslmode=require"

def fix_enum():
    conn = None
    cur = None
    
    try:
        print("🔌 Подключение...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print("✅ Подключено!")
        
        # Откатываем транзакцию
        conn.rollback()
        
        # Проверяем текущие значения
        print("\n📋 Текущие значения orderstatus:")
        cur.execute("SELECT unnest(enum_range(NULL::orderstatus))")
        values = cur.fetchall()
        for v in values:
            print(f"   - {v[0]}")
        
        # Добавляем 'picked_up'
        print("\n📝 Добавляем 'picked_up'...")
        cur.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'picked_up'")
        conn.commit()
        print("✅ 'picked_up' добавлен!")
        
        # Проверяем снова
        print("\n📋 Обновленные значения orderstatus:")
        cur.execute("SELECT unnest(enum_range(NULL::orderstatus))")
        values = cur.fetchall()
        for v in values:
            print(f"   - {v[0]}")
        
        # Обновляем заказ 79
        print("\n🔧 Обновляем заказ #79...")
        cur.execute("UPDATE orders SET status = 'picked_up' WHERE id = 79")
        conn.commit()
        print("✅ Заказ #79 обновлен на 'picked_up'")
        
        # Проверяем
        cur.execute("SELECT id, status FROM orders WHERE id = 79")
        order = cur.fetchone()
        print(f"   Заказ 79: статус = {order[1]}")
        
        print("\n✅ ВСЕ ГОТОВО!")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("\n🔌 Соединение закрыто")

if __name__ == "__main__":
    print("=" * 50)
    print("ДОБАВЛЕНИЕ 'picked_up' В ENUM")
    print("=" * 50)
    fix_enum()