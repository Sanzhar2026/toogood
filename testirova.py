# fix_to_uppercase.py
import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def fix_uppercase():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("=" * 50)
        print("CONVERT STATUSES TO UPPERCASE")
        print("=" * 50)
        
        # Обновляем статусы
        updates = [
            ('pending', 'PENDING'),
            ('confirmed', 'CONFIRMED'),
            ('preparing', 'PREPARING'),
            ('ready_for_pickup', 'READY_FOR_PICKUP'),
            ('picked_up', 'PICKED_UP'),
            ('out_for_delivery', 'OUT_FOR_DELIVERY'),
            ('nearby', 'NEARBY'),
            ('delivered', 'DELIVERED'),
            ('cancelled', 'CANCELLED'),
        ]
        
        for old, new in updates:
            cur.execute(f"UPDATE orders SET status = '{new}' WHERE status = '{old}'")
            print(f"   {old} -> {new}: {cur.rowcount} rows")
        
        # Проверяем
        cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        print("\nOrders by status:")
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print("DONE! All statuses are now UPPERCASE!")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_uppercase()