# fix_order_status.py
import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

def fix_order_status():
    conn = None
    cur = None
    
    try:
        print("🔌 Подключение...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print("✅ Подключено!")
        
        # Начинаем новую транзакцию
        conn.rollback()
        
        # Проверяем текущие значения
        print("\n📋 Текущие значения orderstatus:")
        cur.execute("SELECT unnest(enum_range(NULL::orderstatus))")
        values = cur.fetchall()
        for val in values:
            print(f"   - {val[0]}")
        
        # Проверяем, есть ли 'picked_up'
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumtypid = 'orderstatus'::regtype 
                AND enumlabel = 'picked_up'
            )
        """)
        exists = cur.fetchone()[0]
        
        if not exists:
            print("\n📝 Добавляем 'picked_up'...")
            cur.execute("ALTER TYPE orderstatus ADD VALUE 'picked_up'")
            conn.commit()
            print("✅ Добавлено!")
        else:
            print("\n✅ 'picked_up' уже существует")
        
        # Обновляем заказ 78
        print("\n🔧 Исправляем заказ #78...")
        cur.execute("UPDATE orders SET status = 'out_for_delivery' WHERE id = 78")
        conn.commit()
        print("✅ Заказ #78 обновлен")
        
        # Проверяем
        cur.execute("SELECT id, status FROM orders WHERE id = 78")
        order = cur.fetchone()
        if order:
            print(f"   Заказ 78: статус = {order[1]}")
        
        print("\n✅ Готово!")
        
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
    print("ИСПРАВЛЕНИЕ ENUM orderstatus")
    print("=" * 50)
    fix_order_status()