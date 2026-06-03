# fix_cancelled_final.py
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    trans = conn.begin()
    try:
        # 1. Устанавливаем cancelled_at для отмененных заказов (используем CANCELLED в верхнем регистре)
        result = conn.execute(text("""
            UPDATE orders 
            SET cancelled_at = NOW() 
            WHERE status = 'CANCELLED' AND cancelled_at IS NULL
        """))
        print(f"✅ Обновлено {result.rowcount} заказов (установлен cancelled_at)")
        
        # 2. Удаляем старые отмененные заказы (старше 1 часа)
        result2 = conn.execute(text("""
            DELETE FROM orders 
            WHERE status = 'CANCELLED' 
            AND cancelled_at IS NOT NULL 
            AND cancelled_at < NOW() - INTERVAL '1 hour'
        """))
        print(f"🗑️ Удалено {result2.rowcount} старых отмененных заказов")
        
        # 3. Проверяем результат
        result3 = conn.execute(text("""
            SELECT 
                COUNT(*) as total_cancelled,
                COUNT(CASE WHEN cancelled_at IS NULL THEN 1 END) as without_date,
                COUNT(CASE WHEN cancelled_at IS NOT NULL THEN 1 END) as with_date
            FROM orders 
            WHERE status = 'CANCELLED'
        """))
        row = result3.fetchone()
        print(f"\n📊 Финальная статистика:")
        print(f"  - Всего отмененных: {row[0]}")
        print(f"  - С cancelled_at: {row[2]}")
        print(f"  - Без cancelled_at: {row[1]}")
        
        trans.commit()
        print("\n✅ Готово!")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Ошибка: {e}")