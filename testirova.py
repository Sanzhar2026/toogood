# debug_psycopg2.py
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def debug_psycopg2():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=" * 60)
        print("ДИАГНОСТИКА СТАТУСОВ ЗАКАЗОВ (psycopg2)")
        print("=" * 60)
        
        # 1. Проверяем enum
        print("\n1) Проверка ENUM:")
        cur.execute("SELECT enum_range(NULL::orderstatus)")
        enum_values = cur.fetchone()['enum_range']
        print(f"   ENUM values: {enum_values}")
        
        # 2. Проверяем статусы в таблице orders
        print("\n2) Статусы заказов:")
        cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        for row in cur.fetchall():
            print(f"   {row['status']}: {row['count']}")
        
        # 3. Проверяем структуру таблицы
        print("\n3) Структура таблицы orders:")
        cur.execute("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'orders' AND column_name = 'status'
        """)
        row = cur.fetchone()
        print(f"   column: {row['column_name']}, type: {row['data_type']}, udt_name: {row['udt_name']}")
        
        # 4. Проверяем первые 5 заказов
        print("\n4) Первые 5 заказов:")
        cur.execute("SELECT id, status FROM orders LIMIT 5")
        for row in cur.fetchall():
            print(f"   ID: {row['id']}, Status: {row['status']}, Type: {type(row['status'])}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_psycopg2()