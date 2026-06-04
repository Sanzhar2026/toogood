# check_db_fixed.py
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=" * 60)
    print("📊 СТАТИСТИКА ЗАКАЗОВ")
    print("=" * 60)
    
    # ✅ ИСПОЛЬЗУЕМ ПРАВИЛЬНЫЙ РЕГИСТР (ВЕРХНИЙ)
    result = conn.execute(text("""
        SELECT 
            COUNT(*) FILTER (WHERE status = 'CANCELLED') as cancelled_count,
            COUNT(*) FILTER (WHERE status = 'CONFIRMED') as confirmed_count,
            COUNT(*) FILTER (WHERE status = 'PENDING') as pending_count,
            COUNT(*) FILTER (WHERE status = 'OUT_FOR_DELIVERY') as delivery_count,
            COUNT(*) FILTER (WHERE status = 'DELIVERED') as delivered_count,
            COUNT(*) FILTER (WHERE status = 'nearby') as nearby_count,
            COUNT(*) as total
        FROM orders
    """))
    
    row = result.fetchone()
    print(f"   - CANCELLED: {row[0]}")
    print(f"   - CONFIRMED: {row[1]}")
    print(f"   - PENDING: {row[2]}")
    print(f"   - OUT_FOR_DELIVERY: {row[3]}")
    print(f"   - DELIVERED: {row[4]}")
    print(f"   - nearby: {row[5]}")
    print(f"   - ВСЕГО: {row[6]}")
    
    print("\n" + "=" * 60)
    print("📊 ЗАКАЗЫ С ДОСТАВКОЙ")
    print("=" * 60)
    
    result = conn.execute(text("""
        SELECT delivery_type, COUNT(*) 
        FROM orders 
        GROUP BY delivery_type
    """))
    for row in result:
        print(f"   - {row[0]}: {row[1]} заказов")
    
    print("\n" + "=" * 60)
    print("📊 ОТМЕНЕННЫЕ ЗАКАЗЫ")
    print("=" * 60)
    
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_cancelled,
            COUNT(cancelled_at) as with_date,
            COUNT(*) - COUNT(cancelled_at) as without_date
        FROM orders 
        WHERE status = 'CANCELLED'
    """))
    row = result.fetchone()
    print(f"   - Всего отмененных: {row[0]}")
    print(f"   - С cancelled_at: {row[1]}")
    print(f"   - Без cancelled_at: {row[2]}")
    
    print("\n" + "=" * 60)
    print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 60)