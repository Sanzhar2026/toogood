# fix_existing_orders.py
import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def fix_existing_orders():
    """Исправляет статусы существующих заказов на нижний регистр"""
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cur = conn.cursor()
        
        print("=" * 50)
        print("🔄 ИСПРАВЛЕНИЕ СТАТУСОВ ЗАКАЗОВ")
        print("=" * 50)
        
        # Обновляем статусы с верхнего регистра на нижний
        updates = [
            ('PENDING', 'pending'),
            ('CONFIRMED', 'confirmed'),
            ('PREPARING', 'preparing'),
            ('READY_FOR_PICKUP', 'ready_for_pickup'),
            ('OUT_FOR_DELIVERY', 'out_for_delivery'),
            ('DELIVERED', 'delivered'),
            ('CANCELLED', 'cancelled'),
        ]
        
        for old_status, new_status in updates:
            cur.execute("""
                UPDATE orders 
                SET status = %s::orderstatus 
                WHERE status::text = %s
            """, (new_status, old_status))
            count = cur.rowcount
            if count > 0:
                print(f"   ✅ {old_status} → {new_status}: {count} заказов")
        
        # Специально для picked_up
        cur.execute("""
            UPDATE orders 
            SET status = 'picked_up'::orderstatus 
            WHERE status::text = 'PICKED_UP' OR status::text = 'picked_up'
        """)
        print(f"   ✅ PICKED_UP/picked_up: {cur.rowcount} заказов")
        
        conn.commit()
        
        # Проверяем результат
        print("\n📊 ТЕКУЩИЕ СТАТУСЫ ЗАКАЗОВ:")
        cur.execute("""
            SELECT status::text, COUNT(*) 
            FROM orders 
            GROUP BY status::text 
            ORDER BY status::text
        """)
        for row in cur.fetchall():
            print(f"   • {row[0]}: {row[1]} заказов")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print("✅ Готово!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        if conn:
            conn.rollback()

if __name__ == "__main__":
    fix_existing_orders()