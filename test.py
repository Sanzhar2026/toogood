# final_fix.py
import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def final_fix():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("=" * 60)
        print("FINAL FIX")
        print("=" * 60)
        
        # 1. Проверяем текущий enum
        print("\n1) Current enum:")
        try:
            cur.execute("SELECT enum_range(NULL::orderstatus)")
            print(f"   {cur.fetchone()[0]}")
        except:
            print("   Enum does not exist")
        
        # 2. Удаляем DEFAULT
        print("\n2) Drop DEFAULT...")
        try:
            cur.execute("ALTER TABLE orders ALTER COLUMN status DROP DEFAULT")
            print("   OK")
        except Exception as e:
            print(f"   {e}")
        
        # 3. Меняем на VARCHAR
        print("\n3) Convert to VARCHAR...")
        cur.execute("ALTER TABLE orders ALTER COLUMN status TYPE VARCHAR(50)")
        print("   OK")
        
        # 4. Обновляем статусы
        print("\n4) Update statuses to lowercase...")
        cur.execute("UPDATE orders SET status = LOWER(status)")
        print(f"   Updated {cur.rowcount} rows")
        
        # 5. Удаляем все enum типы
        print("\n5) Drop all enum types...")
        cur.execute("DROP TYPE IF EXISTS orderstatus CASCADE")
        cur.execute("DROP TYPE IF EXISTS orderstatus_old CASCADE")
        cur.execute("DROP TYPE IF EXISTS orderstatus_new CASCADE")
        print("   OK")
        
        # 6. Создаем новый enum
        print("\n6) Create new enum...")
        cur.execute("""
            CREATE TYPE orderstatus AS ENUM (
                'pending', 'confirmed', 'preparing', 
                'ready_for_pickup', 'picked_up', 
                'out_for_delivery', 'nearby', 'delivered', 'cancelled'
            )
        """)
        print("   OK")
        
        # 7. Конвертируем обратно
        print("\n7) Convert to enum...")
        cur.execute("ALTER TABLE orders ALTER COLUMN status TYPE orderstatus USING status::orderstatus")
        print("   OK")
        
        # 8. Восстанавливаем DEFAULT
        print("\n8) Restore DEFAULT...")
        cur.execute("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'pending'")
        print("   OK")
        
        # 9. Проверяем
        print("\n9) Check result:")
        cur.execute("SELECT enum_range(NULL::orderstatus)")
        print(f"   Enum: {cur.fetchone()[0]}")
        
        cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        print("\n   Orders by status:")
        for row in cur.fetchall():
            print(f"      {row[0]}: {row[1]}")
        
        # 10. Проверяем заказы
        cur.execute("SELECT id, status FROM orders LIMIT 5")
        print("\n   Sample orders:")
        for row in cur.fetchall():
            print(f"      Order {row[0]}: {row[1]}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("DONE! Restart backend on Render!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    final_fix()