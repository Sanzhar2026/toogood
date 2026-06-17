# fix_enum_to_uppercase.py
import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def fix_enum_to_uppercase():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("=" * 60)
        print("FIX ENUM TO UPPERCASE")
        print("=" * 60)
        
        # 1. Проверяем текущий enum
        print("\n1) Current enum values:")
        cur.execute("SELECT enum_range(NULL::orderstatus)")
        print(f"   {cur.fetchone()[0]}")
        
        # 2. Меняем тип на VARCHAR
        print("\n2) Convert to VARCHAR...")
        cur.execute("ALTER TABLE orders ALTER COLUMN status TYPE VARCHAR(50)")
        print("   OK")
        
        # 3. Обновляем на UPPERCASE
        print("\n3) Update to UPPERCASE...")
        cur.execute("UPDATE orders SET status = UPPER(status)")
        print(f"   Updated {cur.rowcount} rows")
        
        # 4. Удаляем старый enum
        print("\n4) Drop old enum...")
        cur.execute("DROP TYPE IF EXISTS orderstatus CASCADE")
        print("   OK")
        
        # 5. Создаем новый enum с UPPERCASE
        print("\n5) Create new enum with UPPERCASE...")
        cur.execute("""
            CREATE TYPE orderstatus AS ENUM (
                'PENDING', 'CONFIRMED', 'PREPARING', 
                'READY_FOR_PICKUP', 'PICKED_UP', 
                'OUT_FOR_DELIVERY', 'NEARBY', 'DELIVERED', 'CANCELLED'
            )
        """)
        print("   OK")
        
        # 6. Конвертируем обратно в enum
        print("\n6) Convert back to enum...")
        cur.execute("ALTER TABLE orders ALTER COLUMN status TYPE orderstatus USING status::orderstatus")
        print("   OK")
        
        # 7. Устанавливаем DEFAULT
        print("\n7) Set DEFAULT...")
        cur.execute("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'PENDING'")
        print("   OK")
        
        # 8. Проверяем результат
        print("\n8) Check result:")
        cur.execute("SELECT enum_range(NULL::orderstatus)")
        print(f"   Enum: {cur.fetchone()[0]}")
        
        cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        print("\n   Orders by status:")
        for row in cur.fetchall():
            print(f"      {row[0]}: {row[1]}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("DONE! Enum is now UPPERCASE!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_enum_to_uppercase()